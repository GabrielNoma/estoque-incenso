namespace EstoqueIncenso.Application.Interfaces;

public interface IServicoExportacao
{
    Task<byte[]> GerarExcelAsync(int ano, int mes);
}
