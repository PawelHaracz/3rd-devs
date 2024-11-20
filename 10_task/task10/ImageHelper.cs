using System.Text.RegularExpressions;

namespace task10;

public class ImageHelper
{
    private static readonly Regex ImageUrlPattern = new(
        @"!\[\]\((i/[a-zA-Z0-9_]+\.(png|jpg|jpeg|gif))\)",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);
    
    public async Task<string> ReplaceAllImagesWithContent(string markdown, Func<string, Task<string>> contentGenerator)
    {
        var matches = ImageUrlPattern.Matches(markdown);
        var result = markdown;

        foreach (Match match in matches)
        {
            var imagePath = match.Groups[1].Value;
            var content = await contentGenerator(imagePath);
            var replacement = $"<IMAGE>{content}</IMAGE>{Environment.NewLine}";
            result = result.Replace(match.Value, replacement);
        }

        return result;
    }

    
    
}