# Plan Quality Checklist: F-USER-001

対象フィーチャ:
- ID: F-USER-001
- Epic: EPIC-USER-001-ONBOARDING
- Impl plan: `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/impl-plan.md`

## A. Plan 本体の構造

- [x] `impl-plan.md` が存在し、ファイル先頭のタイトルおよびメタ情報にこの FEATURE-ID と対応する spec へのリンクが明記されている。
- [x] `impl-plan.md` は plan テンプレートの必須セクション（Summary / Technical Context / Constitution Check / Project Structure / Complexity Tracking またはそれに相当する節）をすべて持ち、空欄やダミーテキストが残っていない。
- [x] `impl-plan.md` 内に `NEEDS CLARIFICATION` や同等のプレースホルダが残っていない。

## B. Technical Context / Constitution Check

- [x] Technical Context の各項目（Language/Version, Primary Dependencies, Storage, Testing, Target Platform, Project Type, Performance Goals, Constraints, Scale/Scope）が、このフィーチャの実際の実装方針を具体的に表しており、「未定」や曖昧な表現でごまかされていない。
- [x] Constitution Check セクションに、このフィーチャに適用されるゲート条件が列挙されており、「どのゲートをどのように満たすか」が簡潔に記述されている。
- [x] Constitution Check に列挙されたゲートのうち、満たせないものがある場合は、Complexity Tracking に違反内容と理由、却下した代替案が明記されている。

## C. プロジェクト構造 / 影響範囲

- [x] Project Structure の候補（Single project / Web application / Mobile + API など）から、このフィーチャに実際に採用する構造が 1 つだけ選ばれている。
- [x] 採用しなかった構造のテンプレート文・コメントは `impl-plan.md` から削除されている。
- [x] Project Structure 節で列挙されたディレクトリ/ファイルパスは、リポジトリルートからのパスとして正しく記述されており、「どこに何を置くか」が具体的に伝わる。
- [x] このフィーチャが触る既存モジュールやサービス（例: `services/user-service`, `tests/e2e/...`）があれば、その位置と役割が `impl-plan.md` に明記されている。

## D. 研究・設計成果物との整合性

- [x] `research.md` が存在し、Plan 実行中に解消した主要な不明点ごとに、「Decision / Rationale / Alternatives considered」の 3 点が書かれている。
- [x] `data-model.md` が存在し、このフィーチャが扱うエンティティ・フィールド・関係・バリデーションルールが列挙されている。
- [x] `contracts/` 配下に、このフィーチャで追加・変更される API / メッセージ / イベントの契約が置かれている（形式はプロジェクトの標準に従う。例: OpenAPI, GraphQL schema）。
- [x] `quickstart.md` が存在し、「このフィーチャだけを試す」ための手順（起動コマンド、テストコマンド、確認用の HTTP リクエストなど）が書かれている。
- [x] `impl-plan.md` の記述と `research.md` / `data-model.md` / `contracts/` / `quickstart.md` の内容が矛盾していない（例: Plan に書かれたエンドポイントが contracts にも存在する）。

## E. Epic design index / 他フィーチャとの関係

- [x] このフィーチャが属するエピック配下に `design/index.md` が存在する場合、`impl-plan.md` の Artifacts/Notes または同等の節に `design/index.md` へのパスと役割（feature map, shared entities/APIs, cross-feature flows など）が記載されている。
- [x] このフィーチャが共有エンティティや共有 API を持つ場合、その「所有者」と他フィーチャとの関係が、`design/index.md` または `impl-plan.md` のいずれかで明示されている。

## F. Plan から Tasks へのブレイクダウン準備

- [x] `impl-plan.md` の Plan of Work / Concrete Steps（または同等のセクション）を読むだけで、`/speckit.tasks` が「どのファイルにどのような変更タスクを切るべきか」を機械的に列挙できるレベルの具体性になっている。
- [x] Validation / Acceptance に、「Plan が完了した時点で何をどう実行すると成功か」が具体的なコマンドや HTTP リクエストの形で書かれている。
- [x] Idempotence / Recovery（またはそれに相当する節）に、「途中で失敗した場合のやり直し」「既存環境への影響を最小化する方針」が一度は触れられている。
