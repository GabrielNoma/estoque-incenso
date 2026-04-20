namespace EstoqueIncenso.Domain.Entidades;

public class Funcionaria
{
    public int Id { get; set; }
    public string Nome { get; set; } = string.Empty;
    public bool Ativa { get; set; } = true;

    public ICollection<RegistroDiario> Registros { get; set; } = new List<RegistroDiario>();
}
