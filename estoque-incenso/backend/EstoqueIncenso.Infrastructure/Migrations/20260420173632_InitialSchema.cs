using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace EstoqueIncenso.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class InitialSchema : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "funcionarias",
                columns: table => new
                {
                    id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    nome = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    ativa = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_funcionarias", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "registros_diarios",
                columns: table => new
                {
                    id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    funcionaria_id = table.Column<int>(type: "integer", nullable: false),
                    data = table.Column<DateOnly>(type: "date", nullable: false),
                    quantidade = table.Column<int>(type: "integer", nullable: true),
                    falta = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    motivo_falta = table.Column<string>(type: "text", nullable: true),
                    observacao_falta = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_registros_diarios", x => x.id);
                    table.CheckConstraint("chk_exclusividade", "NOT (quantidade IS NOT NULL AND falta = TRUE)");
                    table.CheckConstraint("chk_motivo_quando_falta", "(falta = FALSE AND motivo_falta IS NULL) OR (falta = TRUE AND motivo_falta IS NOT NULL)");
                    table.CheckConstraint("chk_obs_quando_outro", "motivo_falta != 'Outro' OR (motivo_falta = 'Outro' AND observacao_falta IS NOT NULL AND observacao_falta != '')");
                    table.CheckConstraint("chk_quantidade_positiva", "quantidade >= 0 OR quantidade IS NULL");
                    table.ForeignKey(
                        name: "FK_registros_diarios_funcionarias_funcionaria_id",
                        column: x => x.funcionaria_id,
                        principalTable: "funcionarias",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "uq_funcionaria_nome",
                table: "funcionarias",
                column: "nome",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "uq_registro_funcionaria_data",
                table: "registros_diarios",
                columns: new[] { "funcionaria_id", "data" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "registros_diarios");

            migrationBuilder.DropTable(
                name: "funcionarias");
        }
    }
}
