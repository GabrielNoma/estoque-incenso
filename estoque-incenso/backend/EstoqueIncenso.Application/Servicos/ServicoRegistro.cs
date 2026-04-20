using EstoqueIncenso.Application.DTOs;
using EstoqueIncenso.Application.Interfaces;
using EstoqueIncenso.Domain.Entidades;
using EstoqueIncenso.Domain.Enums;
using Microsoft.Extensions.Logging;

namespace EstoqueIncenso.Application.Servicos;

public class ServicoRegistro : IServicoRegistro
{
    private readonly IRepositorioRegistro _repositorioRegistro;
    private readonly IRepositorioFuncionaria _repositorioFuncionaria;
    private readonly ILogger<ServicoRegistro> _logger;

    public ServicoRegistro(
        IRepositorioRegistro repositorioRegistro,
        IRepositorioFuncionaria repositorioFuncionaria,
        ILogger<ServicoRegistro> logger)
    {
        _repositorioRegistro = repositorioRegistro;
        _repositorioFuncionaria = repositorioFuncionaria;
        _logger = logger;
    }

    public async Task<GradeMensalDto> MontarGradeMensalAsync(int ano, int mes)
    {
        _logger.LogInformation("Montando grade mensal para {Mes}/{Ano}", mes, ano);

        var registros = await _repositorioRegistro.ListarPorMesAsync(ano, mes);
        var funcionariasAtivas = await _repositorioFuncionaria.ListarAsync(incluirInativas: false);

        // Funcionárias inativas que possuem registros no mês (histórico)
        var idsFuncionariasComRegistros = registros
            .Select(r => r.FuncionariaId)
            .Distinct()
            .ToHashSet();

        var idsFuncionariasAtivas = funcionariasAtivas
            .Select(f => f.Id)
            .ToHashSet();

        // IDs de inativas que têm registros no mês (precisam aparecer na grade histórica)
        var idsFuncionariasInativasComRegistros = idsFuncionariasComRegistros
            .Except(idsFuncionariasAtivas)
            .ToHashSet();

        var funcionariasInativasComRegistros = registros
            .Where(r => idsFuncionariasInativasComRegistros.Contains(r.FuncionariaId))
            .Select(r => r.Funcionaria)
            .DistinctBy(f => f.Id);

        var todasFuncionarias = funcionariasAtivas
            .Concat(funcionariasInativasComRegistros)
            .OrderBy(f => f.Nome);

        var registrosPorFuncionaria = registros
            .GroupBy(r => r.FuncionariaId)
            .ToDictionary(g => g.Key, g => g.ToList());

        var funcionariasDto = todasFuncionarias.Select(f =>
        {
            var registrosDaFuncionaria = registrosPorFuncionaria.TryGetValue(f.Id, out var lista)
                ? lista.Select(ParaRegistroDiarioDto)
                : Enumerable.Empty<RegistroDiarioDto>();

            return new FuncionariaComRegistrosDto(f.Id, f.Nome, f.Ativa, registrosDaFuncionaria);
        });

        return new GradeMensalDto(ano, mes, funcionariasDto);
    }

    public async Task<RegistroSalvoDto> SalvarOuAtualizarAsync(UpsertRegistroDto dto)
    {
        _logger.LogInformation(
            "Salvando registro para FuncionariaId: {FuncionariaId}, Data: {Data}",
            dto.FuncionariaId, dto.Data);

        ValidarRegrasDeNegocio(dto);

        var funcionaria = await _repositorioFuncionaria.BuscarPorIdAsync(dto.FuncionariaId);
        if (funcionaria is null)
        {
            _logger.LogWarning("Funcionária não encontrada: Id {FuncionariaId}", dto.FuncionariaId);
            throw new KeyNotFoundException($"Funcionária com Id {dto.FuncionariaId} não encontrada.");
        }

        var motivoFalta = ConverterMotivoFalta(dto.MotivoFalta);

        var registro = new RegistroDiario
        {
            FuncionariaId = dto.FuncionariaId,
            Data = dto.Data,
            Quantidade = dto.Quantidade,
            Falta = dto.Falta,
            MotivoFalta = motivoFalta,
            ObservacaoFalta = dto.ObservacaoFalta
        };

        var salvo = await _repositorioRegistro.CriarOuAtualizarAsync(registro);

        _logger.LogInformation("Registro salvo com Id: {Id}", salvo.Id);

        return ParaRegistroSalvoDto(salvo);
    }

    public async Task ExcluirAsync(int id)
    {
        _logger.LogInformation("Excluindo registro Id: {Id}", id);
        await _repositorioRegistro.ExcluirAsync(id);
    }

    // ── Validações de negócio ─────────────────────────────────────────────────

    private void ValidarRegrasDeNegocio(UpsertRegistroDto dto)
    {
        if (dto.Quantidade is not null && dto.Falta)
        {
            _logger.LogWarning(
                "Violação de regra: quantidade e falta informados simultaneamente. FuncionariaId: {Id}",
                dto.FuncionariaId);
            throw new InvalidOperationException(
                "Quantidade e falta não podem ser informados simultaneamente.");
        }

        if (dto.Falta && dto.MotivoFalta is null)
        {
            _logger.LogWarning(
                "Violação de regra: falta sem motivo. FuncionariaId: {Id}", dto.FuncionariaId);
            throw new InvalidOperationException(
                "Motivo é obrigatório quando há falta.");
        }

        if (string.Equals(dto.MotivoFalta, "outro", StringComparison.OrdinalIgnoreCase)
            && string.IsNullOrWhiteSpace(dto.ObservacaoFalta))
        {
            _logger.LogWarning(
                "Violação de regra: motivo 'outro' sem observação. FuncionariaId: {Id}",
                dto.FuncionariaId);
            throw new InvalidOperationException(
                "Observação é obrigatória quando motivo é 'outro'.");
        }
    }

    // ── Conversões ────────────────────────────────────────────────────────────

    /// <summary>
    /// Converte a string do contrato da API ("atestado", "falta", "outro")
    /// para o enum interno <see cref="MotivoFalta"/>. Retorna null quando a string é null.
    /// </summary>
    private static MotivoFalta? ConverterMotivoFalta(string? motivo)
    {
        if (motivo is null) return null;

        return motivo.ToLowerInvariant() switch
        {
            "atestado" => Domain.Enums.MotivoFalta.Atestado,
            "falta"    => Domain.Enums.MotivoFalta.Falta,
            "outro"    => Domain.Enums.MotivoFalta.Outro,
            _ => throw new InvalidOperationException(
                $"Motivo de falta inválido: '{motivo}'. Valores aceitos: atestado, falta, outro.")
        };
    }

    /// <summary>
    /// Converte o enum interno para a string do contrato da API (lowercase).
    /// </summary>
    private static string? ConverterMotivoFaltaParaString(MotivoFalta? motivo) =>
        motivo switch
        {
            Domain.Enums.MotivoFalta.Atestado => "atestado",
            Domain.Enums.MotivoFalta.Falta    => "falta",
            Domain.Enums.MotivoFalta.Outro    => "outro",
            null => null,
            _    => null
        };

    private static RegistroDiarioDto ParaRegistroDiarioDto(RegistroDiario r) =>
        new(r.Id, r.Data, r.Quantidade, r.Falta,
            ConverterMotivoFaltaParaString(r.MotivoFalta), r.ObservacaoFalta);

    private static RegistroSalvoDto ParaRegistroSalvoDto(RegistroDiario r) =>
        new(r.Id, r.FuncionariaId, r.Data, r.Quantidade, r.Falta,
            ConverterMotivoFaltaParaString(r.MotivoFalta), r.ObservacaoFalta);
}
