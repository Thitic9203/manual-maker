# Source Map — doc-type → แหล่งที่บังคับ (ห้ามมโน)

Every doc-type maps to **the authoritative source its real values must come from**. At intake the skill
shows the expected source for the chosen doc-type and asks for the link/file/JQL. **No source (or a
source that does not cover a required value) → the run stops for that doc-type.** A placeholder is never
filled with a guess.

The "ข้อมูลหลักที่ต้องกรอก" column is copied from the scaffold's own index page (page `3693641732`) —
it is what each doc-type's page structure already asks for. The "แหล่งที่บังคับ" column is what this
skill requires before it will write.

| Doc-type (หน้าลูก) | ข้อมูลหลักที่ต้องกรอก | แหล่งที่บังคับ (authoritative) |
|---|---|---|
| PRD — Product Requirement Documents | No., Feature, Reference, flags, PIC, BRD status | Jira filter ต่อ subsystem (OLS 21689 / ELMS 21690 / CBMS 21691 / EvMS 21692) + ลิงก์ BRD/PRD จริง |
| High Level Business Requirements | intro + หน้าลูกราย module | BRD/business spec จริงต่อ module (ไฟล์/หน้า Confluence ที่ผู้ใช้ให้) |
| BRD Sample — per module | requirement ราย module | เอกสาร BRD ของ module นั้น |
| Technical Document | Overview, Architecture, API Spec, Data Dictionary, Sequence | Tech spec / repo / ADR ของ feature นั้น |
| API Documentation | endpoints, request/response, auth | **OpenAPI/Swagger หรือ route definitions ใน repo** — ไม่ถอดจากความจำ |
| Data Dictionary & ER Diagram | Entity, Column, Type, Null, Key, Description | **DB schema จริง** (migration / Prisma / SQL DDL) — ER มาจาก schema เดียวกัน |
| Use Case & Sequence Diagram | actors, steps, sequence | flow/spec จริง หรือ code path |
| Error / Event / PII Documentation | error codes / events / PII fields | repo (error map / event catalog) หรือ spec; PII จาก data classification จริง |
| Enterprise Architecture (EA) | System landscape, Integration map, Standards | architecture doc / C4 / diagram source จริง |
| Master Data | Entity, Field, Type, Source of truth, Owner | DB schema + ทะเบียน master data / owner จริง |
| Jira Board & Ticket Template | Issue types, Workflow, DoD, Labels, Naming, Estimation | การตั้งค่า Jira project จริง (board/workflow) |
| Template - Troubleshooting article | Problem, Solution, panel, Related | known-issues / support log จริง — ไม่มี = ข้าม (ห้ามมโนปัญหา) |
| Knowledge Sharing | หัวข้อ + หน้าลูก | เนื้อหาที่ทีมให้ |
| Meeting notes / Minutes of Meeting | Date, Attendees, Agenda, Action items | **บันทึกประชุมจริง** (ไฟล์/โน้ต) — ไม่แต่ง action item |
| QA Documents | WOW, matrix, test mgmt, automation | เอกสาร QA / test management จริง |
| Bug Priority & Severity Matrix | priority × severity | มาตรฐาน QA ของทีมจริง |
| Test Management & Test Cases | test cases, coverage | test suite / test management tool จริง |
| AI & Data Documentation | Model, Pipeline, Dataset, Feature store | เอกสาร/registry ของ model/pipeline จริง |
| Integration Documents | Source, Target, Protocol, Direction, Auth | integration inventory / config จริง |
| Sprint Review | Goal, Demo items, Feedback, Next steps | บันทึก sprint review จริง |
| DevOps Documents | Environments, pipeline, alerts, runbook | CI/CD config, infra, monitoring จริง |
| Deliverable Checklist | checklist เอกสารที่ต้องมี | นิยาม deliverable ของทีมจริง |
| User Manual | Overview, Getting started, Feature guides, FAQ | ระบบจริง + แหล่งที่ผู้ใช้ให้ (ทำแบบ text ในสกิลนี้; ถ้าต้องภาพ+วงแดง ใช้ manual-maker) |
| Risk & Issue Logs | ID, Type, Impact, Likelihood, Mitigation, Owner | ทะเบียนความเสี่ยงจริง |
| Wording Guideline | Term, คำที่ใช้, คำที่เลี่ยง | รายการ term ที่ทีมล็อก (แหล่ง locked-term ของทั้ง space) |
| Open Questions | No., Question, Raised by, Status, Answer | รายการคำถามค้างจริง |
| Pre-grooming | Ticket, Open questions, Ready? | Jira ticket จริงก่อน grooming |
| Education Path | Context, Requirement, Scope, AC | requirement intake จริง |
| AI Platform / Data Platform | Component, Purpose, Owner | สถาปัตยกรรม platform จริง |
| Docs — Zoho / GWS / SonarQube / Qualys | Tool, Purpose, Doc link | คู่มือ/หน้าเครื่องมือภายนอกจริง |

## Rules that ride this map

- **The map names a *category* of source, not the value.** The skill still reads the actual
  file/URL/JQL the user provides and extracts values from it. A category alone is not a source.
- **Subsystem is always a dimension**, so most sources are read **per subsystem** (four Jira filters,
  four schema scopes, …) and land as rows tagged in the `Subsystem` column.
- **A doc-type whose source is legitimately "ไม่มี"** (e.g. Troubleshooting with no known-issues list)
  → the section is **omitted**, exactly as `manual-maker` omits an unsourced chapter. Never invented.
- When a value the page asks for is not in the provided source → **STOP and ask**; do not approximate.
