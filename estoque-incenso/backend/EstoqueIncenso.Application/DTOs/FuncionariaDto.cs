namespace EstoqueIncenso.Application.DTOs;

public record FuncionariaDto(int Id, string Nome, bool Ativa);

public record CriarFuncionariaDto(string Nome);

public record AtualizarFuncionariaDto(string Nome);

public record AtualizarStatusDto(bool Ativa);
