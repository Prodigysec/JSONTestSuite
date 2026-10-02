using System;
using System.IO;
using System.Text;
using Newtonsoft.Json;

if (args.Length != 1)
{
    Console.Error.WriteLine($"Usage: {Path.GetFileName(Environment.GetCommandLineArgs()[0])} file.json");
    return 2;
}

try
{
    using var fileStream = new FileStream(args[0], FileMode.Open);
    using var streamReader = new StreamReader(fileStream, new UTF8Encoding(false, true),
                                            detectEncodingFromByteOrderMarks: false);
    using var jsonReader = new JsonTextReader(streamReader);
    try
    {
        if (!jsonReader.Read()) return 1;
        var serializer = JsonSerializer.Create(new JsonSerializerSettings {
            MaxDepth = 512, CheckAdditionalContent = true
        });
        serializer.Deserialize(jsonReader);
        return 0;
    }
    catch (JsonException e)
    {
        Console.Error.WriteLine(e);
        return 1;
    }
    catch (DecoderFallbackException e)
    {
        Console.Error.WriteLine(e);
        return 1;
    }
}
catch (Exception e)
{
    Console.Error.WriteLine(e);
    return 2;
}
