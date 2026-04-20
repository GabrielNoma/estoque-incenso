using System.Text.Json;

namespace EstoqueIncenso.Api.Middleware;

public class MidlwareExcecoes
{
    private readonly RequestDelegate _next;
    private readonly ILogger<MidlwareExcecoes> _logger;

    public MidlwareExcecoes(RequestDelegate next, ILogger<MidlwareExcecoes> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (KeyNotFoundException ex)
        {
            _logger.LogWarning(ex, "Recurso não encontrado: {Mensagem}", ex.Message);
            await EscreverRespostaAsync(context, StatusCodes.Status404NotFound, ex.Message);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "Operação inválida: {Mensagem}", ex.Message);
            await EscreverRespostaAsync(context, StatusCodes.Status400BadRequest, ex.Message);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erro inesperado: {Mensagem}\n{StackTrace}", ex.Message, ex.StackTrace);
            await EscreverRespostaAsync(context, StatusCodes.Status500InternalServerError,
                "Ocorreu um erro interno no servidor.");
        }
    }

    private static async Task EscreverRespostaAsync(HttpContext context, int statusCode, string mensagem)
    {
        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/json";

        var resposta = JsonSerializer.Serialize(new { erro = mensagem });
        await context.Response.WriteAsync(resposta);
    }
}
