using System.Diagnostics.CodeAnalysis;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Containers;
using Xunit.Abstractions;

namespace task10;
//
[Experimental("SKEXP0010")]
public class Test(ITestOutputHelper output) : IAsyncLifetime
{
    // private readonly IContainer _qdrant = new ContainerBuilder()
    //     .WithImage("qdrant/qdrant:v1.12.4")
    //     .WithPortBinding(6334, 6334)
    //     .WithPortBinding(6333, 6333)
    //     .WithVolumeMount("qdrant_storage", "/qdrant/storage:z")
    //     .WithWaitStrategy(Wait.ForUnixContainer().UntilHttpRequestIsSucceeded(r => r.ForPort(6333)))
    //     .Build();

    private readonly ArxivKernel _kernel = new();
    
    [Fact]
    public async Task Test1()
    {
        await _kernel.ProcessDocuments("https://centrala.ag3nts.org/dane/","arxiv-draft.html", "", true);
        
    }

    [Fact]
    public async Task Test2()
    {
        var questions = new[]
        {
            "jakiego owocu użyto podczas pierwszej próby transmisji materii w czasie?",
            "Na rynku którego miasta wykonano testową fotografię użytą podczas testu przesyłania multimediów?",
            "Co Bomba chciał znaleźć w Grudziądzu?",
            "Resztki jakiego dania zostały pozostawione przez Rafała?",
            "Od czego pochodzą litery BNW w nazwie nowego modelu językowego?"
        };

        for (int i = 0; i < questions.Length; i++)
        {
            var q = questions[i];
            var answer = await _kernel.AnswerForQuestion(q);
            output.WriteLine($"{i+1}: {answer}");
        }
    }
    

    public Task InitializeAsync()
    {
        return Task.CompletedTask;
        // return _qdrant.StartAsync();
    }

    public Task DisposeAsync()
    {
        return Task.CompletedTask;
        // return _qdrant.DisposeAsync().AsTask();
    }
}
