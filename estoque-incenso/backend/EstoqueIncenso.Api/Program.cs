using EstoqueIncenso.Api.Middleware;
using EstoqueIncenso.Application.Interfaces;
using EstoqueIncenso.Application.Servicos;
using EstoqueIncenso.Infrastructure.Dados;
using EstoqueIncenso.Infrastructure.Repositorios;
using Microsoft.EntityFrameworkCore;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

// ── Controllers ────────────────────────────────────────────────────────────
builder.Services.AddControllers();

// ── OpenAPI / Swagger ──────────────────────────────────────────────────────
builder.Services.AddOpenApi();
builder.Services.AddEndpointsApiExplorer();

// ── Banco de dados ─────────────────────────────────────────────────────────
builder.Services.AddDbContext<ContextoBancoDados>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// ── CORS ───────────────────────────────────────────────────────────────────
var allowAnyOrigin = builder.Configuration.GetValue<bool>("Cors:AllowAnyOrigin");

builder.Services.AddCors(options =>
{
    if (allowAnyOrigin)
    {
        options.AddDefaultPolicy(policy =>
            policy.AllowAnyOrigin()
                  .AllowAnyMethod()
                  .AllowAnyHeader());
    }
    else
    {
        var allowedOrigin = builder.Configuration["Cors:AllowedOrigin"] ?? string.Empty;
        options.AddDefaultPolicy(policy =>
            policy.WithOrigins(allowedOrigin)
                  .AllowAnyMethod()
                  .AllowAnyHeader());
    }
});

// ── DI: Repositórios ───────────────────────────────────────────────────────
builder.Services.AddScoped<IRepositorioFuncionaria, RepositorioFuncionaria>();
builder.Services.AddScoped<IRepositorioRegistro, RepositorioRegistro>();

// ── DI: Serviços ───────────────────────────────────────────────────────────
builder.Services.AddScoped<IServicoFuncionaria, ServicoFuncionaria>();
builder.Services.AddScoped<IServicoRegistro, ServicoRegistro>();
builder.Services.AddScoped<IServicoExportacao, ServicoExportacao>();

// ──────────────────────────────────────────────────────────────────────────
var app = builder.Build();

// ── Middleware de exceções (deve ser o primeiro) ───────────────────────────
app.UseMiddleware<MidlwareExcecoes>();

// ── Swagger apenas em dev ──────────────────────────────────────────────────
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference();
}

// ── CORS ───────────────────────────────────────────────────────────────────
app.UseCors();

// ── Arquivos estáticos (Angular publicado em wwwroot/) ────────────────────
app.UseDefaultFiles();
app.UseStaticFiles();

// ── HTTPS Redirect ─────────────────────────────────────────────────────────
app.UseHttpsRedirection();

// ── Autorização (sem autenticação — rede local) ───────────────────────────
app.UseAuthorization();

// ── Rotas dos controllers ──────────────────────────────────────────────────
app.MapControllers();

// ── Fallback para Angular SPA (quando não é chamada de API) ───────────────
app.MapFallbackToFile("index.html");

app.Run();
