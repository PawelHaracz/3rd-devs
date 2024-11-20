using System.ClientModel;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Text;
using Qdrant.Client;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace task10;

public class ArxivKernel
{
    private readonly Kernel _kernel;
    
    [Experimental("SKEXP0010")]
    public ArxivKernel()
    {
        TokenCredential credentials = new DefaultAzureCredential(new DefaultAzureCredentialOptions());
        // var aiCredentials = new AzureOpenAIClient(new Uri("https://cloudtown-io.openai.azure.com"), credentials);
        var aiCredentials = new AzureOpenAIClient(new Uri("https://cloudtown-io.openai.azure.com"),
            new ApiKeyCredential(Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY")!));
        var builder = Kernel.CreateBuilder();
        builder.Services.AddHttpClient();
        builder.AddQdrantVectorStore("localhost", serviceId:"localhost");
        builder.AddAzureOpenAIChatCompletion("gpt-4o", aiCredentials, "azure");
        builder.AddAzureOpenAITextEmbeddingGeneration("text-embedding-3-large", aiCredentials, serviceId:"azure",  dimensions: 3072);
        builder.AddAzureOpenAIAudioToText("whisper", aiCredentials, serviceId: "azure");
        builder.Services.AddSingleton<ImageHelper>();
   
        _kernel = builder.Build();
        
    }

    [Experimental("SKEXP0001")]
    public async Task ProcessDocuments(string url, string pageUrl, string apiKey, bool useCache = false)
    {
        const string localCache = "items.cache";
        FireCrawlResponse? parsedItem;
        var factory = _kernel.GetRequiredService<IHttpClientFactory>();

        if (!useCache)
        {

            var httpClient = factory.CreateClient();
            httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
            var items = await httpClient.PostAsync("https://api.firecrawl.dev/v1/scrape",
                JsonContent.Create(new
                    {
                        url = $"{url}/{pageUrl}",
                        formats = new[] { "markdown", "links" }
                    }
                ));
            items.EnsureSuccessStatusCode();
            await using var response = await items.Content.ReadAsStreamAsync();
            parsedItem = await JsonSerializer.DeserializeAsync<FireCrawlResponse>(response, JsonSerializerOptions.Web);
            await using var f = new FileStream(localCache, FileMode.OpenOrCreate, FileAccess.Write);
            response.Seek(0, SeekOrigin.Begin);
            await response.CopyToAsync(f);
        }
        else
        {
            await using var fr = new FileStream(localCache, FileMode.Open, FileAccess.Read);
            parsedItem = await JsonSerializer.DeserializeAsync<FireCrawlResponse>(fr, JsonSerializerOptions.Web);
        }
        

        if (parsedItem is null)
        {
            return;
        }

        var chunks = TextChunker.SplitMarkdownParagraphs(parsedItem.Data.Markdown.Split("#"), 1_000, 100, "");
        
        var imageHelper = _kernel.GetRequiredService<ImageHelper>();
        var listParsedImages = new List<string>();
        foreach (var chunk in chunks)
        {
            var newChunk = await imageHelper.ReplaceAllImagesWithContent(chunk, async imagePath =>
            {
                var chat = _kernel.GetRequiredService<IChatCompletionService>("azure");
        
                var history = new ChatHistory();
                history.AddSystemMessage(
                    "You are a friendly and helpful assistant that responds to questions directly");
        
                var message = new ChatMessageContentItemCollection
                {
                    new TextContent(
                        "Can you do a detail analysis and tell me all the minute details that present in this image?"),
                    new ImageContent(new Uri($"{url}/{imagePath}"))
                };
        
                history.AddUserMessage(message);
        
                var result = await chat.GetChatMessageContentAsync(history);
        
                return result.Content ?? chunk;
            });
        
            listParsedImages.Add(newChunk);
        }
        var audioToTextService = _kernel.GetRequiredService<IAudioToTextService>("azure");
        foreach (var link in parsedItem.Data.Links)
        {
            await using var audioFileStream = await DownloadAudioFileAsync(link);
            var audioFileBinaryData = await BinaryData.FromStreamAsync(audioFileStream);
            var fileExtension = Path.GetExtension(link).ToLowerInvariant();
            var mimeType = GetMimeType(fileExtension);
            var audioContent = new AudioContent(audioFileBinaryData, mimeType: mimeType);
            var textContent = await audioToTextService.GetTextContentAsync(
                audioContent, 
                new OpenAIAudioToTextExecutionSettings()
                {
                    Language = "pl",
                    ResponseFormat = "json"
                });
            if (textContent.Text != null) 
                listParsedImages.Add(textContent.Text);
        }
        
        var vectorStore = _kernel.GetRequiredService<IVectorStore>("localhost");
        var collection = vectorStore.GetCollection<Guid, Docs>("docs1");
        if (await collection.CollectionExistsAsync() == false)
        {
            await collection.CreateCollectionAsync();
        }
        
        var embeddings = _kernel.GetRequiredService<ITextEmbeddingGenerationService>("azure");
        foreach (var parsedImage in listParsedImages)
        {
            var embedding = await embeddings.GenerateEmbeddingsAsync([parsedImage]);
            foreach (var memory in embedding)
            {
                await collection.UpsertAsync(new Docs()
                {
                   Id = Guid.CreateVersion7(),
                   Content = parsedImage,
                   Embedding = memory,
                });
            }
        }
    }
    
    [Experimental("SKEXP0001")]
    public async Task<string> AnswerForQuestion(string question)
    {
        var embeddings = _kernel.GetRequiredService<ITextEmbeddingGenerationService>("azure");
        var questionEmbedding = await embeddings.GenerateEmbeddingsAsync([question]);
        
        var vectorStore = _kernel.GetRequiredService<IVectorStore>("localhost");
        var collection = vectorStore.GetCollection<Guid, Docs>("docs1");
        var searchResult = await collection.VectorizedSearchAsync(questionEmbedding.First(), new() { Top = 3 });

        var contents = new List<string>();
        await foreach (var rag in searchResult.Results)
        {
            contents.Add(rag.Record.Content);
        }
        
        var chat = _kernel.GetRequiredService<IChatCompletionService>("azure");
        var history = new ChatHistory();
        
        history.AddSystemMessage(@"You are a helpful assistant that answers questions based on the provided context. 
            If you cannot find the answer in the context, say that you don't have enough information to answer the question.
            Always base your answers on the provided context and be specific about where the information comes from.
            
            <rules>            
            - ALWAYS output a valid JSON object with keys: ""_thoughts"", ""answer""
            - ALWAYS output valid JSON starting with { and ending with } (skip markdown block quotes)
            - Include ""_thoughts"" property first, followed by ""answer"" 
            - ""_thoughts"" should contain concise, step-by-step analysis of query formulation
            - ""answer"" MUST contain your answer
            - Your answer should a short one sentence with correct answer for the received question
            - Your answer should be in Polish language.
            </rules>

            ");
            
        var context = string.Join("\n\n", contents);
        history.AddUserMessage($"Context:\n{context}\n\nQuestion: {question}");
        
        var result = await chat.GetChatMessageContentAsync(history);
        if (result.Content != null)
        {
            byte[] contentByte = Encoding.UTF8.GetBytes(result.Content);
            await using var contentStream = new MemoryStream(contentByte);
            var content = await JsonSerializer.DeserializeAsync<AiAnswer>(contentStream);
            return content?.answer?? "Sorry, I couldn't generate an answer." ; 
        }

        return "Sorry, I couldn't generate an answer.";
    }
    
    public class FireCrawlResponse
    {
        public FireCrawlResponseData Data { get; set; }
    }

    public class FireCrawlResponseData
    {
        public string Markdown { get; set; }
        public IEnumerable<string> Links { get; set; }
    }
    
    private async Task<Stream> DownloadAudioFileAsync(string audioUrl)
    {
        var factory = _kernel.GetRequiredService<IHttpClientFactory>();
        using var httpClient = factory.CreateClient();
        var response = await httpClient.GetAsync(audioUrl);
        response.EnsureSuccessStatusCode();
    
        var memoryStream = new MemoryStream();
        await response.Content.CopyToAsync(memoryStream);
        memoryStream.Position = 0;
    
        return memoryStream;
    }
    
    private string GetMimeType(string fileExtension)
    {
        return fileExtension switch
        {
            ".mp3" => "audio/mpeg",
            ".wav" => "audio/wav",
            _ => throw new ArgumentException($"Unsupported audio format: {fileExtension}. Only MP3 and WAV are supported.")
        };
    }
}

public class AiAnswer
{
    public string _thoughts { get; set; }
    public string answer { get; set; }
}
