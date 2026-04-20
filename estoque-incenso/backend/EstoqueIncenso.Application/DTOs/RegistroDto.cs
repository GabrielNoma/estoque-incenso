namespace EstoqueIncenso.Application.DTOs;

/// <summary>Dados de um único registro diário retornado ao cliente.</summary>
public record RegistroDiarioDto(
    int Id,
    DateOnly Data,
    int? Quantidade,
    bool Falta,
    string? MotivoFalta,
    string? ObservacaoFalta
);

/// <summary>Funcionária com todos os seus registros do mês consultado.</summary>
public record FuncionariaComRegistrosDto(
    int Id,
    string Nome,
    bool Ativa,
    IEnumerable<RegistroDiarioDto> Registros
);

/// <summary>Grade mensal completa: todas as funcionárias relevantes com seus registros.</summary>
public record GradeMensalDto(
    int Ano,
    int Mes,
    IEnumerable<FuncionariaComRegistrosDto> Funcionarias
);

/// <summary>Payload de entrada para criar ou atualizar um registro (upsert por FuncionariaId+Data).</summary>
public record UpsertRegistroDto(
    int FuncionariaId,
    DateOnly Data,
    int? Quantidade,
    bool Falta,
    string? MotivoFalta,
    string? ObservacaoFalta
);

/// <summary>Confirmação de registro salvo retornado ao cliente após PUT.</summary>
public record RegistroSalvoDto(
    int Id,
    int FuncionariaId,
    DateOnly Data,
    int? Quantidade,
    bool Falta,
    string? MotivoFalta,
    string? ObservacaoFalta
);
