import type { TestEntityRepository } from "../repository";
import type { TestEntityRelationalExecutor } from "./contracts";
import { rejectedStoredTestEntity, testEntityFromRow, testEntityValues } from "./mapping";

const columns = "id, integer_value, uuid_value, occurred_at, label, status, enabled, categories, notes, description, reviewed_at, secondary_categories, visibility, lifecycle, created_at, updated_at";
const names = columns.split(", ");

/** App-specific SQL only, not an ORM. The target validates/quotes __SCHEMA__.
 * get includes deleted state for restore; ordinary services filter it. */
export function relationalTestEntityRepository(executor: TestEntityRelationalExecutor): TestEntityRepository {
  return {
    async get(id) {
      const result = await executor.execute({ text: `SELECT ${columns} FROM __SCHEMA__.test_entity WHERE id = $1`, values: [id] }, "read");
      if (!result.ok) throw result.error;
      if (result.value.rows.length === 0) return null;
      const mapped = result.value.rows.length === 1 ? testEntityFromRow(result.value.rows[0]!) : rejectedStoredTestEntity();
      if (!mapped.ok) throw mapped.error;
      return mapped.value;
    },
    async create(entity) {
      const result = await executor.execute({
        text: `INSERT INTO __SCHEMA__.test_entity (${columns}) VALUES (${names.map((_, index) => "$" + (index + 1)).join(", ")}) RETURNING ${columns}`,
        values: testEntityValues(entity),
      }, "create");
      if (!result.ok) return result;
      return result.value.rowCount === 1 && result.value.rows.length === 1 ? testEntityFromRow(result.value.rows[0]!) : rejectedStoredTestEntity();
    },
    async save(entity) {
      const mutable = names.filter(name => name !== "created_at");
      const result = await executor.execute({
        text: `UPDATE __SCHEMA__.test_entity SET ${mutable.slice(1).map((name, index) => name + " = $" + (index + 2)).join(", ")} WHERE id = $1 RETURNING ${columns}`,
        values: testEntityValues(entity).filter((_, index) => names[index] !== "created_at"),
      }, "write");
      if (!result.ok) return result;
      return result.value.rowCount === 1 && result.value.rows.length === 1 ? testEntityFromRow(result.value.rows[0]!) : rejectedStoredTestEntity();
    },
    async listByStatus(status) {
      const result = await executor.execute({ text: `SELECT ${columns} FROM __SCHEMA__.test_entity WHERE status = $1 AND lifecycle->>'state' = 'active' ORDER BY created_at, id`, values: [status] }, "read");
      if (!result.ok) throw result.error;
      const entities = [];
      for (const row of result.value.rows) {
        const mapped = testEntityFromRow(row);
        if (!mapped.ok) throw mapped.error;
        entities.push(mapped.value);
      }
      return entities;
    },
  };
}
