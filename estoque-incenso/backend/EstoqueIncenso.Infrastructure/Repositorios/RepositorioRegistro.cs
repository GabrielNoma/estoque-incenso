using EstoqueIncenso.Application.Interfaces;
using EstoqueIncenso.Domain.Entidades;
using EstoqueIncenso.Infrastructure.Dados;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace EstoqueIncenso.Infrastructure.Repositorios;

public class RepositorioRegistro : IRepositorioRegistro
{
    private readonly ContextoBancoDados _contexto;
    private readonly ILogger<RepositorioRegistro> _logger;

    public RepositorioRegistro(ContextoBancoDados contexto, ILogger<RepositorioRegistro> logger)
    {
        _contexto = contexto;
        _logger = logger;
    }

    public async Task<IEnumerable<RegistroDiario>> ListarPorMesAsync(int ano, int mes)
    {
        _logger.LogInformation("Listando registros do mês {Mes}/{Ano}", mes, ano);

        var inicio = new DateOnly(ano, mes, 1);
        var fim = inicio.AddMonths(1).AddDays(-1);

        return await _contexto.RegistrosDiarios
            .Include(r => r.Funcionaria)
            .Where(r => r.Data >= inicio && r.Data <= fim)
            .OrderBy(r => r.FuncionariaId)
            .ThenBy(r => r.Data)
            .ToListAsync();
    }

    public async Task<RegistroDiario?> BuscarPorFuncionariaEDataAsync(int funcionariaId, DateOnly data)
    {
        _logger.LogInformation(
            "Buscando registro para FuncionariaId: {FuncionariaId}, Data: {Data}",
            funcionariaId, data);

        return await _contexto.RegistrosDiarios
            .FirstOrDefaultAsync(r => r.FuncionariaId == funcionariaId && r.Data == data);
    }

    public async Task<RegistroDiario> CriarOuAtualizarAsync(RegistroDiario registro)
    {
        var existente = await BuscarPorFuncionariaEDataAsync(registro.FuncionariaId, registro.Data);

        if (existente is null)
        {
            _logger.LogInformation(
                "Criando registro para FuncionariaId: {FuncionariaId}, Data: {Data}",
                registro.FuncionariaId, registro.Data);

            _contexto.RegistrosDiarios.Add(registro);
            await _contexto.SaveChangesAsync();
            return registro;
        }

        _logger.LogInformation(
            "Atualizando registro Id: {Id} para FuncionariaId: {FuncionariaId}, Data: {Data}",
            existente.Id, registro.FuncionariaId, registro.Data);

        existente.Quantidade = registro.Quantidade;
        existente.Falta = registro.Falta;
        existente.MotivoFalta = registro.MotivoFalta;
        existente.ObservacaoFalta = registro.ObservacaoFalta;

        await _contexto.SaveChangesAsync();
        return existente;
    }

    public async Task ExcluirAsync(int id)
    {
        _logger.LogInformation("Excluindo registro Id: {Id}", id);

        var registro = await _contexto.RegistrosDiarios.FindAsync(id);

        if (registro is null)
        {
            _logger.LogWarning("Registro não encontrado para exclusão: Id {Id}", id);
            throw new KeyNotFoundException($"Registro com Id {id} não encontrado.");
        }

        _contexto.RegistrosDiarios.Remove(registro);
        await _contexto.SaveChangesAsync();
    }
}
