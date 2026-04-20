using EstoqueIncenso.Domain.Entidades;
using EstoqueIncenso.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace EstoqueIncenso.Infrastructure.Dados;

public class ContextoBancoDados : DbContext
{
    public ContextoBancoDados(DbContextOptions<ContextoBancoDados> options) : base(options)
    {
    }

    public DbSet<Funcionaria> Funcionarias => Set<Funcionaria>();
    public DbSet<RegistroDiario> RegistrosDiarios => Set<RegistroDiario>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Funcionaria
        modelBuilder.Entity<Funcionaria>(entity =>
        {
            entity.ToTable("funcionarias");
            entity.HasKey(f => f.Id);
            entity.Property(f => f.Id).ValueGeneratedOnAdd();
            entity.Property(f => f.Nome)
                .IsRequired()
                .HasMaxLength(100);
            entity.Property(f => f.Ativa)
                .IsRequired()
                .HasDefaultValue(true);
            entity.HasIndex(f => f.Nome)
                .IsUnique()
                .HasDatabaseName("uq_funcionaria_nome");
        });

        // RegistroDiario
        modelBuilder.Entity<RegistroDiario>(entity =>
        {
            entity.ToTable("registros_diarios", t =>
            {
                // CHECK: quantidade >= 0
                t.HasCheckConstraint("chk_quantidade_positiva",
                    "quantidade >= 0 OR quantidade IS NULL");

                // CHECK: Quantidade e Falta = true são mutuamente exclusivos
                t.HasCheckConstraint("chk_exclusividade",
                    "NOT (quantidade IS NOT NULL AND falta = TRUE)");

                // CHECK: MotivoFalta obrigatório quando Falta = true
                t.HasCheckConstraint("chk_motivo_quando_falta",
                    "(falta = FALSE AND motivo_falta IS NULL) OR (falta = TRUE AND motivo_falta IS NOT NULL)");

                // CHECK: ObservacaoFalta obrigatória quando MotivoFalta = 'Outro'
                t.HasCheckConstraint("chk_obs_quando_outro",
                    "motivo_falta != 'Outro' OR (motivo_falta = 'Outro' AND observacao_falta IS NOT NULL AND observacao_falta != '')");
            });

            entity.HasKey(r => r.Id);
            entity.Property(r => r.Id).ValueGeneratedOnAdd();

            entity.Property(r => r.FuncionariaId).IsRequired();
            entity.Property(r => r.Data).IsRequired();
            entity.Property(r => r.Quantidade).IsRequired(false);
            entity.Property(r => r.Falta)
                .IsRequired()
                .HasDefaultValue(false);
            entity.Property(r => r.ObservacaoFalta)
                .HasMaxLength(500)
                .IsRequired(false);

            // MotivoFalta persistido como string (enum)
            entity.Property(r => r.MotivoFalta)
                .HasConversion<string>()
                .IsRequired(false);

            // Unique constraint: uma linha por funcionária por dia
            entity.HasIndex(r => new { r.FuncionariaId, r.Data })
                .IsUnique()
                .HasDatabaseName("uq_registro_funcionaria_data");

            // Relacionamento com Funcionaria (sem cascade delete — preservar histórico)
            entity.HasOne(r => r.Funcionaria)
                .WithMany(f => f.Registros)
                .HasForeignKey(r => r.FuncionariaId)
                .OnDelete(DeleteBehavior.Restrict);
        });
    }
}
