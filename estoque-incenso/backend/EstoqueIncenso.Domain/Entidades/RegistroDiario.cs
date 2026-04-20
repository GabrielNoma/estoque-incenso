using EstoqueIncenso.Domain.Enums;

namespace EstoqueIncenso.Domain.Entidades;

public class RegistroDiario
{
    public int Id { get; set; }
    public int FuncionariaId { get; set; }
    public DateOnly Data { get; set; }
    public int? Quantidade { get; set; }
    public bool Falta { get; set; } = false;
    public MotivoFalta? MotivoFalta { get; set; }
    public string? ObservacaoFalta { get; set; }

    public Funcionaria Funcionaria { get; set; } = null!;
}
