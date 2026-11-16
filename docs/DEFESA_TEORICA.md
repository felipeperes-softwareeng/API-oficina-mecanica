
# Defesa Teórica — Banco de Dados e Persistência

**Projeto:** Oficina Mecânica — Sistema Web com Flask e SQLite  
**Repositório:** https://github.com/felipeperes-softwareeng/API-oficina-mecanica  
**Tema:** Modelagem relacional, SQL nativo, CRUD e integração com Flask

---

## 1. Visão geral do banco de dados

O sistema foi desenvolvido em Python com Flask e utiliza SQLite como banco de dados relacional.

O esquema do banco está no arquivo `schema.sql`, enquanto as operações SQL estão concentradas em `db_sql.py`, mantendo a persistência separada das rotas da aplicação (`app.py`).

O modelo contém três entidades:

| Tabela | Função | Chave primária |
|---|---|---|
| `cliente` | Armazena os dados dos clientes | `id` |
| `veiculo` | Armazena os veículos dos clientes | `id` |
| `ordem_servico` | Armazena os serviços dos veículos | `id` |

O Diagrama Entidade-Relacionamento (DER) está disponível em `docs/DER_oficina_mecanica.png`.

### Relacionamentos 1:N

**Cliente → Veículos**

Um cliente pode possuir zero ou vários veículos, mas cada veículo pertence a exatamente um cliente.

**Veículo → Ordens de Serviço**

Um veículo pode possuir zero ou várias ordens de serviço, mas cada ordem de serviço pertence a exatamente um veículo.

Esses relacionamentos são implementados utilizando as chaves estrangeiras:

- `veiculo.cliente_id`
- `ordem_servico.veiculo_id`

O CRUD completo da interface web foi implementado para clientes e veículos. A tabela `ordem_servico` está estruturada no banco e pode receber operações SQL, mas ainda não possui rotas e telas próprias.

---

## 2. Questão 1 — Qual a diferença entre INNER JOIN e LEFT JOIN?

### Resposta teórica

O `INNER JOIN` retorna apenas os registros que possuem correspondência entre as duas tabelas relacionadas.

Já o `LEFT JOIN` retorna todos os registros da tabela à esquerda, mesmo quando não existe um registro correspondente na tabela à direita.

Quando não existe correspondência, os campos da tabela à direita recebem `NULL`.

### Aplicação no projeto

#### INNER JOIN — Listagem de veículos

Arquivo: `db_sql.py`  
Função: `listar_veiculos()`

```sql
SELECT v.*, c.nome AS cliente_nome
FROM veiculo v
JOIN cliente c ON c.id = v.cliente_id
ORDER BY v.placa;
```

Essa consulta retorna os veículos cadastrados juntamente com o nome de seus respectivos proprietários.

Utilizamos `JOIN`, que nesse caso equivale a `INNER JOIN`.

Como cada veículo possui obrigatoriamente um cliente válido, a consulta combina os registros das duas tabelas.

#### LEFT JOIN — Listagem de clientes

Arquivo: `db_sql.py`  
Função: `listar_clientes()`

```sql
SELECT c.*, COUNT(v.id) AS total_veiculos
FROM cliente c
LEFT JOIN veiculo v ON v.cliente_id = c.id
GROUP BY c.id
ORDER BY c.nome;
```

Essa consulta retorna todos os clientes, inclusive aqueles que ainda não possuem veículos cadastrados.

O `LEFT JOIN` mantém esses clientes no resultado, enquanto `COUNT(v.id)` retorna zero quando não existem veículos relacionados.

### Exemplo prático

Considere a seguinte situação:

| Cliente | Veículos cadastrados |
|---|---|
| Ana | 2 |
| Bruno | 0 |
| Carlos | 1 |

Com `INNER JOIN`, Bruno não apareceria, pois não possui veículos associados.

Com `LEFT JOIN`, os três clientes aparecem normalmente, incluindo Bruno com zero veículos.

### Resposta curta para a apresentação

> O INNER JOIN retorna apenas os registros que possuem correspondência nas duas tabelas. Já o LEFT JOIN mantém todos os registros da tabela da esquerda, mesmo que não tenham correspondência. No nosso projeto, usamos INNER JOIN para listar veículos com seus proprietários e LEFT JOIN para mostrar todos os clientes, inclusive aqueles que ainda não possuem veículos cadastrados.

---

## 3. Questão 2 — ON DELETE CASCADE e ON DELETE SET NULL

### Resposta teórica

As chaves estrangeiras garantem a integridade referencial entre as tabelas.

Quando um registro principal é excluído, a configuração `ON DELETE` determina o comportamento dos registros dependentes.

### ON DELETE CASCADE

O `ON DELETE CASCADE` exclui automaticamente os registros dependentes quando o registro principal é apagado.

Por exemplo, se um cliente for excluído, todos os veículos vinculados a esse cliente também serão excluídos.

### ON DELETE SET NULL

O `ON DELETE SET NULL` preserva os registros dependentes, mas altera suas chaves estrangeiras para `NULL`.

Por exemplo, se um cliente for excluído, seus veículos permaneceriam cadastrados, porém sem um proprietário associado.

**Importante:** para utilizar `ON DELETE SET NULL`, a coluna da chave estrangeira precisa permitir valores nulos. Se estiver configurada como `NOT NULL`, a exclusão não poderá atribuir `NULL` sem violar essa restrição.

### Aplicação no projeto

No arquivo `schema.sql`, utilizamos `ON DELETE CASCADE` nos dois relacionamentos.

#### Relacionamento Cliente → Veículo

```sql
FOREIGN KEY (cliente_id)
REFERENCES cliente (id)
ON DELETE CASCADE
```

#### Relacionamento Veículo → Ordem de Serviço

```sql
FOREIGN KEY (veiculo_id)
REFERENCES veiculo (id)
ON DELETE CASCADE
```

### O que acontece ao excluir um cliente?

1. O cliente é removido da tabela `cliente`.
2. Todos os veículos pertencentes a ele são excluídos automaticamente.
3. Todas as ordens de serviço associadas a esses veículos também são excluídas.

Essa exclusão em cadeia é aplicada pelo próprio SQLite, não sendo necessário executar manualmente um comando `DELETE` para cada tabela dependente.

### O que acontece ao excluir um veículo?

O veículo é excluído e suas ordens de serviço também são removidas automaticamente. O cliente proprietário continua cadastrado.

### Por que escolhemos CASCADE?

Porque, no modelo desenvolvido nesta etapa, veículos e ordens de serviço são tratados como registros dependentes de seus respectivos registros principais.

A aplicação também apresenta uma confirmação antes da exclusão, avisando que os registros relacionados serão removidos.

Em um sistema comercial real, seria importante avaliar a preservação do histórico de serviços por razões administrativas, fiscais ou legais. Para esse cenário, poderiam ser consideradas outras estratégias, como exclusão lógica ou restrição de exclusão.

### Ativação das chaves estrangeiras no SQLite

No arquivo `db_sql.py`, a função `get_db()` executa:

```python
g.sql.execute("PRAGMA foreign_keys = ON")
```

Esse comando habilita a aplicação das regras de chaves estrangeiras na conexão SQLite.

Sem essa configuração, a integridade referencial pode não ser aplicada pelo SQLite.

### Resposta curta para a apresentação

> No nosso sistema, utilizamos ON DELETE CASCADE. Quando um cliente é excluído, seus veículos são apagados automaticamente e, consequentemente, as ordens de serviço desses veículos também são removidas. Já ON DELETE SET NULL manteria os registros dependentes e apenas removeria o vínculo, atribuindo NULL à chave estrangeira. Como nossas chaves estrangeiras possuem NOT NULL, seria necessário modificar o banco para utilizar SET NULL.

---

## 4. Questões complementares

### 4.1. Por que utilizamos banco de dados relacional?

Porque nosso sistema trabalha com entidades que possuem relacionamentos bem definidos.

Clientes possuem veículos, e veículos possuem ordens de serviço.

O modelo relacional facilita a organização das informações e permite garantir a consistência dos dados por meio de chaves primárias, estrangeiras e restrições.

### 4.2. O que é PRIMARY KEY?

É uma chave utilizada para identificar exclusivamente cada registro de uma tabela.

No projeto, cada cliente, veículo e ordem de serviço possui um campo `id` como chave primária.

### 4.3. O que é FOREIGN KEY?

É uma chave estrangeira que cria um relacionamento entre tabelas.

Por exemplo, `cliente_id` na tabela `veiculo` referencia o campo `id` da tabela `cliente`.

Isso impede, quando as restrições estão ativadas, que um veículo seja vinculado a um cliente inexistente.

### 4.4. O que são Constraints?

São regras aplicadas ao banco de dados para garantir a integridade das informações.

Utilizamos:

- `PRIMARY KEY`: identifica unicamente um registro.
- `FOREIGN KEY`: estabelece relacionamentos.
- `NOT NULL`: impede valores nulos em campos obrigatórios.
- `UNIQUE`: impede valores duplicados.
- `CHECK`: valida condições específicas dos dados.

Por exemplo, o campo `placa` possui `UNIQUE`, evitando veículos com placas repetidas.

O campo `ano` possui `CHECK`, impedindo anos inferiores a 1900 quando informados.

### 4.5. Como implementamos o CRUD?

O CRUD é composto por quatro operações:

| Operação | Comando SQL | Aplicação |
|---|---|---|
| Create | `INSERT` | Cadastrar clientes e veículos |
| Read | `SELECT` | Consultar e listar dados |
| Update | `UPDATE` | Editar registros existentes |
| Delete | `DELETE` | Excluir registros |

As rotas ficam em `app.py`, enquanto os comandos SQL são executados pelas funções de `db_sql.py`.

### 4.6. Por que separamos app.py e db_sql.py?

Para aplicar o princípio de separação de responsabilidades.

O arquivo `app.py` gerencia as rotas, recebe os dados enviados pelos formulários, realiza validações e retorna as páginas HTML.

O arquivo `db_sql.py` centraliza a conexão com o banco e as operações SQL.

Essa organização melhora a manutenção, facilita os testes e evita misturar lógica de interface com persistência de dados.

### 4.7. Como funciona o comando flask init-db?

Utilizamos a biblioteca Click, integrada ao Flask, para registrar um comando personalizado.

No arquivo `db_sql.py`, o comando `init-db` chama a função `init_db()`, que lê o arquivo `schema.sql` e executa as instruções de criação das tabelas.

Para executar:

```bash
flask --app app init-db
```

**Atenção:** o arquivo `schema.sql` contém instruções `DROP TABLE IF EXISTS`. Portanto, executar novamente o comando recria as tabelas e apaga os dados existentes.

### 4.8. Como protegemos as consultas contra SQL Injection?

Utilizamos consultas parametrizadas, passando os valores por meio de `?` em vez de concatenar diretamente os dados fornecidos pelo usuário.

Exemplo:

```python
get_db().execute(
    "SELECT * FROM cliente WHERE id = ?",
    (cliente_id,)
)
```

Isso impede que valores fornecidos pelo usuário sejam interpretados como comandos SQL dentro desses parâmetros.

### 4.9. Como o projeto pode ser testado?

O repositório possui os arquivos:

- `testar_db_sql.py`
- `testar_crud.py`
- `testes.sql`

Os testes verificam operações CRUD, validações, relacionamentos e restrições do banco.

Para executar os testes Python:

```bash
python testar_db_sql.py
python testar_crud.py
```

Os dois scripts Python utilizam bancos temporários, evitando modificar o banco principal.

A aprovação deve ser confirmada pela execução dos testes no ambiente local.

---

## 5. Roteiro para apresentação oral

### Integrante 1 — Modelagem do banco

> Nosso projeto é um sistema de oficina mecânica desenvolvido utilizando Python, Flask e SQLite. Criamos três tabelas: cliente, veículo e ordem de serviço. O nosso DER apresenta dois relacionamentos um-para-muitos. Um cliente pode possuir vários veículos, e um veículo pode possuir várias ordens de serviço. Também utilizamos chaves primárias, estrangeiras e restrições para garantir a integridade dos dados.

### Integrante 2 — INNER JOIN e LEFT JOIN

> Em nossas consultas utilizamos dois tipos de JOIN. O INNER JOIN é utilizado para listar os veículos com seus respectivos proprietários, retornando apenas registros com correspondência. Já o LEFT JOIN permite mostrar todos os clientes, mesmo aqueles que não possuem veículos cadastrados. Nesse caso, utilizamos também COUNT para apresentar a quantidade de veículos de cada cliente.

### Integrante 3 — CASCADE e SET NULL

> Para garantir a integridade referencial, configuramos as chaves estrangeiras com ON DELETE CASCADE. Assim, quando um cliente é excluído, seus veículos e as respectivas ordens de serviço também são apagados. Se utilizássemos ON DELETE SET NULL, os registros dependentes permaneceriam no banco, mas perderiam o vínculo com o registro principal. No entanto, isso exigiria permitir valores nulos nas nossas chaves estrangeiras.

### Integrante 4 — Integração com Flask

> Organizamos o projeto separando as rotas no arquivo app.py e as operações do banco no arquivo db_sql.py. Implementamos o CRUD utilizando SQL nativo, com INSERT, SELECT, UPDATE e DELETE. Também criamos um comando personalizado com Click, chamado flask init-db, que lê nosso arquivo schema.sql e cria as tabelas. Dessa forma, conseguimos integrar o banco de dados à interface web de maneira organizada.

---

## 6. Conclusão

O projeto Oficina Mecânica demonstra a aplicação prática dos conceitos de banco de dados relacionais integrados ao Flask.

Foram implementados:

- Modelagem de entidades e relacionamentos 1:N.
- Criação de tabelas com SQL nativo.
- Chaves primárias, estrangeiras e restrições.
- CRUD funcional de clientes e veículos.
- Consultas utilizando INNER JOIN e LEFT JOIN.
- Integridade referencial com ON DELETE CASCADE.
- Separação das operações de persistência em db_sql.py.
- Inicialização do banco por comando personalizado com Click.
- Scripts de testes para validação das funcionalidades.

A estrutura atende aos requisitos práticos da etapa acadêmica de Banco de Dados e Persistência, permitindo demonstrar tanto o funcionamento do sistema quanto os conceitos teóricos utilizados em sua implementação.

---

**Arquivos de referência:** `docs/DER_oficina_mecanica.png`, `schema.sql`, `db_sql.py`, `app.py`, `testar_db_sql.py`, `testar_crud.py` e `testes.sql`.
