using EstoqueIncenso.Application.DTOs;

namespace EstoqueIncenso.Application.Interfaces;

public interface IServicoRegistro
{
    /// <summary>
    /// Retorna a grade mensal com todas as funcionárias ativas
    /// e inativas que possuam registros no mês informado.
    /// </summary>
    Task<GradeMensalDto> MontarGradeMensalAsync(int ano, int mes);

    /// <summary>
    /// Cria ou atualiza um registro diário (upsert por FuncionariaId+Data).
    /// Lança <see cref="InvalidOperationException"/> quando as regras de negócio são violadas
    /// e <see cref="KeyNotFoundException"/> quando a funcionária não existe.
    /// </summary>
    Task<RegistroSalvoDto> SalvarOuAtualizarAsync(UpsertRegistroDto dto);

    /// <summary>
    /// Remove um registro pelo Id.
    /// Lança <see cref="KeyNotFoundException"/> quando o registro não existe.
    /// </summary>
    Task ExcluirAsync(int id);
}
