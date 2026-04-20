using EstoqueIncenso.Application.DTOs;
using EstoqueIncenso.Application.Interfaces;
using EstoqueIncenso.Domain.Entidades;
using Microsoft.Extensions.Logging;

namespace EstoqueIncenso.Application.Servicos;

public class ServicoFuncionaria : IServicoFuncionaria
{
    private readonly IRepositorioFuncionaria _repositorio;
    private readonly ILogger<ServicoFuncionaria> _logger;

    public ServicoFuncionaria(IRepositorioFuncionaria repositorio, ILogger<ServicoFuncionaria> logger)
    {
        _repositorio = repositorio;
        _logger = logger;
    }

    public async Task<IEnumerable<FuncionariaDto>> ListarAsync(bool incluirInativas)
    {
        _logger.LogInformation("Listando funcionárias. IncluirInativas: {IncluirInativas}", incluirInativas);

        var funcionarias = await _repositorio.ListarAsync(incluirInativas);
        return funcionarias.Select(ParaDto);
    }

    public async Task<FuncionariaDto> CriarAsync(CriarFuncionariaDto dto)
    {
        _logger.LogInformation("Criando funcionária: {Nome}", dto.Nome);

        var nomeExiste = await _repositorio.ExisteComNomeAsync(dto.Nome);
        if (nomeExiste)
        {
            _logger.LogWarning("Tentativa de criar funcionária com nome duplicado: {Nome}", dto.Nome);
            throw new InvalidOperationException("Já existe uma funcionária com este nome.");
        }

        var funcionaria = new Funcionaria
        {
            Nome = dto.Nome.Trim(),
            Ativa = true
        };

        var criada = await _repositorio.CriarAsync(funcionaria);
        _logger.LogInformation("Funcionária criada com Id: {Id}", criada.Id);

        return ParaDto(criada);
    }

    public async Task<FuncionariaDto> AtualizarAsync(int id, AtualizarFuncionariaDto dto)
    {
        _logger.LogInformation("Atualizando funcionária Id: {Id}, Novo nome: {Nome}", id, dto.Nome);

        var funcionaria = await _repositorio.BuscarPorIdAsync(id);
        if (funcionaria is null)
        {
            _logger.LogWarning("Funcionária não encontrada: {Id}", id);
            throw new KeyNotFoundException("Funcionária não encontrada.");
        }

        var nomeExiste = await _repositorio.ExisteComNomeAsync(dto.Nome, excluirId: id);
        if (nomeExiste)
        {
            _logger.LogWarning("Tentativa de renomear funcionária para nome duplicado: {Nome}", dto.Nome);
            throw new InvalidOperationException("Já existe uma funcionária com este nome.");
        }

        funcionaria.Nome = dto.Nome.Trim();
        var atualizada = await _repositorio.AtualizarAsync(funcionaria);

        return ParaDto(atualizada);
    }

    public async Task<FuncionariaDto> AlterarStatusAsync(int id, bool ativa)
    {
        _logger.LogInformation("Alterando status da funcionária Id: {Id} para Ativa: {Ativa}", id, ativa);

        var funcionaria = await _repositorio.BuscarPorIdAsync(id);
        if (funcionaria is null)
        {
            _logger.LogWarning("Funcionária não encontrada: {Id}", id);
            throw new KeyNotFoundException("Funcionária não encontrada.");
        }

        funcionaria.Ativa = ativa;
        var atualizada = await _repositorio.AtualizarAsync(funcionaria);

        return ParaDto(atualizada);
    }

    private static FuncionariaDto ParaDto(Funcionaria f) =>
        new(f.Id, f.Nome, f.Ativa);
}
