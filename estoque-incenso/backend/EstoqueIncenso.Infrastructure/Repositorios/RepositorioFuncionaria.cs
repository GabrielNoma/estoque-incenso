using EstoqueIncenso.Application.Interfaces;
using EstoqueIncenso.Domain.Entidades;
using EstoqueIncenso.Infrastructure.Dados;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace EstoqueIncenso.Infrastructure.Repositorios;

public class RepositorioFuncionaria : IRepositorioFuncionaria
{
    private readonly ContextoBancoDados _contexto;
    private readonly ILogger<RepositorioFuncionaria> _logger;

    public RepositorioFuncionaria(ContextoBancoDados contexto, ILogger<RepositorioFuncionaria> logger)
    {
        _contexto = contexto;
        _logger = logger;
    }

    public async Task<IEnumerable<Funcionaria>> ListarAsync(bool incluirInativas)
    {
        _logger.LogInformation("Listando funcionárias. IncluirInativas: {IncluirInativas}", incluirInativas);

        var consulta = _contexto.Funcionarias.AsQueryable();

        if (!incluirInativas)
            consulta = consulta.Where(f => f.Ativa);

        return await consulta
            .OrderBy(f => f.Nome)
            .ToListAsync();
    }

    public async Task<Funcionaria?> BuscarPorIdAsync(int id)
    {
        _logger.LogInformation("Buscando funcionária por Id: {Id}", id);
        return await _contexto.Funcionarias.FindAsync(id);
    }

    public async Task<bool> ExisteComNomeAsync(string nome, int? excluirId = null)
    {
        var consulta = _contexto.Funcionarias
            .Where(f => f.Nome.ToLower() == nome.ToLower());

        if (excluirId.HasValue)
            consulta = consulta.Where(f => f.Id != excluirId.Value);

        return await consulta.AnyAsync();
    }

    public async Task<Funcionaria> CriarAsync(Funcionaria funcionaria)
    {
        _logger.LogInformation("Criando funcionária: {Nome}", funcionaria.Nome);
        _contexto.Funcionarias.Add(funcionaria);
        await _contexto.SaveChangesAsync();
        return funcionaria;
    }

    public async Task<Funcionaria> AtualizarAsync(Funcionaria funcionaria)
    {
        _logger.LogInformation("Atualizando funcionária Id: {Id}", funcionaria.Id);
        _contexto.Funcionarias.Update(funcionaria);
        await _contexto.SaveChangesAsync();
        return funcionaria;
    }
}
