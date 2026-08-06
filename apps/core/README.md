# Engineering Design Document — `core` App

**Project:** UniAGORA Backend
**App:** `apps.core`
**Status:** Revised per CTO review, round 1 — resubmitted for sign-off
**Document type:** Permanent technical reference
**Audience:** Future maintainers, reviewers, and engineers implementing the domain apps that follow `core` in the build order

---

## 0. Revision History

### Round 1 — CTO Review Response

CTO review approved the app "with minor revisions." Five review comments were addressed; none required a change to the frozen PRD, Architecture, or DDS, and none changed `core`'s public responsibilities.

| # | Review comment | Resolution |
|---|---|---|
| 1 | Replace `.pk == .pk` comparison with Django model equality (`==`) in `IsOwnerVendor.has_object_permission` | **Changed.** See §5.3. |
| 2 | Re-evaluate whether `IsOwnerVendor.has_permission()` is necessary; justify or remove | **Removed**, after re-evaluation concluded the override duplicated composition-level responsibility for a non-security benefit. See §5.3 for the full reasoning. |
| 3 | Compare the `ActiveUniversityFilterBackend` empty-queryset default against raising `PermissionDenied`/`ValidationError`; strengthen documentation | **Retained**, with the requested comparison now documented in full in `filters.py` and summarized in §6. |
| 4 | Document `_resolve_vendor_profile`'s extensibility for future vendor-owned model shapes | **Documentation-only change.** See §5.3. |
| 5 | Future submissions should include the complete `tests/` directory, actual terminal test output, coverage output, and lint output | **Acknowledged as a standing process requirement** for every app from this point forward; this submission includes all four (§8, §10). |

No architectural redesign occurred. No class was renamed, added, or removed from the set Architecture §8 specifies. Changes were strictly scoped to the five items above.

---

This document explains the architecture, implementation, and rationale of the `core` app without requiring the reader to inspect source code, following the same format as the approved `common` app EDD.

---

## 1. Purpose of the `core` App

`core` is the **domain-aware cross-cutting concerns** layer of the UniAGORA backend. It exists so that every domain-owning app (`vendors`, `stores`, `products`, `chat`, `reviews`, `reports`, etc.) shares one single, consistent implementation of:

- role-based and ownership-based permission logic, and
- university-scoping query filtering,

instead of each domain app reimplementing "is this user a verified vendor?" or "does this belong to the user's university?" independently and drifting apart over time — the same motivation that justifies `common`, one layer below.

**Explicit Requirement.** Backend Architecture §1 (Final Project Structure) names `core` directly:

```
├── core/                      # Domain-aware cross-cutting concerns
│   ├── permissions.py         #   IsAuthenticatedCustomer, IsVerifiedVendor,
│   │                          #   IsOwnerVendor, IsAdmin
│   └── filters.py             #   ActiveUniversityFilterBackend
```

Every file, class name, and one-line responsibility in this document traces back to that block, plus Architecture §2 (Final App Boundaries) and §8 (Permission Architecture).

---

## 2. Responsibilities and Architectural Boundaries

### What `core` owns

| Component | File |
|---|---|
| `IsAuthenticatedCustomer` | `permissions.py` |
| `IsVerifiedVendor` | `permissions.py` |
| `IsOwnerVendor` | `permissions.py` |
| `IsAdmin` | `permissions.py` |
| `ActiveUniversityFilterBackend` | `filters.py` |

### What `core` explicitly does NOT own

| Excluded concern | Where it actually lives | Why |
|---|---|---|
| Any persisted model or migration | Each owning domain app | Architecture §2: `core`'s "Does NOT own" column reads "Models, migrations." |
| Business rules (vendor suspension cascade, review eligibility, listing expiry, etc.) | Each domain app's service layer | Architecture §7: "all business logic in `services.py`/`services/` per app." `core` enforces *access*, never *business outcomes*. |
| The response envelope, exception handling, pagination, generic media fields | `common` | Already implemented and approved — `core` does not duplicate it (see `common` app EDD §2). |
| Enums (`VendorStatus`, `ProductStatus`, etc.) | Each owning domain app | Same reasoning the `common` EDD applies to itself (§2): centralizing domain enums in a lower, domain-agnostic-or-cross-cutting layer would leak domain knowledge upward into a layer that must stay generic across every consumer. |
| API endpoints, serializers, admin registration | N/A — not applicable to this app | See §7 below. |

**The governing test** (identical to the one the `common` EDD applies to itself): *does this file need to import from, or reason about, a specific domain model?* For `core`, the answer is intentionally **yes** — that is precisely what distinguishes it from `common` (Architecture §1: `common` is "Pure generic infra — zero domain knowledge"; `core` is "Domain-aware cross-cutting concerns"). The distinguishing question for `core` specifically is narrower: *does this reasoning belong to request-time access control / query scoping, or to a business outcome?* Only the former belongs here.

---

## 3. Fit Into the Overall Backend Architecture

```
        ┌──────────────────────────────────────────────────────────┐
        │  vendors / stores / products / chat / reviews / reports /  │
        │  notifications / users / universities / admin_dashboard    │
        └───────────────────────────┬──────────────────────────────┘
                                     │ imports permissions/filters from
                                     ▼
                                  ┌──────┐
                                  │ core │  (domain-aware permissions, filters)
                                  └───┬──┘
                                      │ imports from
                                      ▼
                                  ┌────────┐
                                  │ common │  (zero domain knowledge)
                                  └────────┘
```

Per the Backend Architecture's dependency rule: *"`core` may import domain models (`User`, `VendorProfile`, `University`) but nothing imports `core` circularly — it sits directly above domain apps, below nothing except `common`."* In practice this means: domain apps import `core.permissions`/`core.filters` for use in their views, and `core`'s own logic reasons about domain model *attributes* (see §5 for exactly how, and why no domain model is actually imported by name).

This matches the confirmed build order: `common` + `core` are implemented first and second, precisely because every subsequent app depends on them.

---

## 4. Directory and File Structure

```
apps/core/
├── __init__.py
├── apps.py             CoreConfig (AppConfig registration — structural only, see §7)
├── permissions.py       IsAuthenticatedCustomer, IsVerifiedVendor, IsOwnerVendor, IsAdmin
├── filters.py           ActiveUniversityFilterBackend
├── README.md            This document
└── tests/
    ├── __init__.py
    ├── test_permissions.py
    └── test_filters.py
```

No `models.py`, no `migrations/`, no `serializers.py`, no `views.py`/`urls.py`, no `admin.py` — see §7 for the explicit reasoning behind each omission.

---

## 5. Permission Classes

All four classes are defined in `permissions.py`, subclassing `rest_framework.permissions.BasePermission`.

### 5.1 `IsAuthenticatedCustomer`

Base authenticated-user check. PRD §4: *"Every registered account is automatically a Customer."* There is no separate Customer model, table, or role flag anywhere in the DDS, so this permission checks nothing beyond authentication (`request.user.is_authenticated`). It exists as its own named class — rather than every view importing DRF's stock `IsAuthenticated` directly — so call sites read in domain language and stay consistent with Architecture §8, which names it as a first-class permission alongside the vendor/admin checks.

**Classification: Explicit Requirement** (Architecture §8).

### 5.2 `IsVerifiedVendor`

Authenticated user who additionally owns a `VendorProfile` whose status is `VERIFIED`.

Implementation relies on two documented attributes, accessed purely by name:
- `user.vendor_profile` — the reverse accessor implied by `VendorProfile.user` (`OneToOneField`, DDS §4.3).
- `vendor_profile.is_verified` — a documented model property, `status == VERIFIED` (DDS §4.3: *"`is_verified` property (`status == VERIFIED`)"*).

Because `is_verified` is defined purely in terms of `status == VERIFIED`, a `SUSPENDED` vendor automatically and correctly fails this check with zero extra logic in `core` — matching the PRD's suspension behavior (§5) and the DDS's suspension cascade (§9.2) without `core` needing to know the full `VendorStatus` enum at all.

**Classification: Explicit Requirement** (Architecture §8).

### 5.3 `IsOwnerVendor`

Object-level permission: the requesting user's own `VendorProfile` is the one that owns the target object — either directly (`Store`, DDS §4.5) or transitively through its `Store` (`Product`, DDS §4.7 → §4.5).

Architecture §8, verbatim: *"Never trusts a vendor/store ID from the request body."* Ownership is derived **exclusively** from `request.user`'s own vendor profile; no client-supplied vendor/store identifier (URL kwarg, query parameter, or request body field) is ever consulted. This is tested explicitly (`test_object_level_ignores_client_supplied_identifiers`).

Exactly one method is implemented — `has_object_permission` — matching Architecture §8's literal scoping of this class as strictly object-level. It resolves the object's owning `VendorProfile` via a small internal helper (`_resolve_vendor_profile`), then compares the resolved profile to the requester's own profile with `==` rather than a manual `.pk == .pk` comparison (**CTO review, round 1, item 1**) — Django's `Model.__eq__` already compares primary key and concrete model class, so `==` is the idiomatic form and avoids reaching into `.pk` by hand.

**`has_permission()` — considered and removed (CTO review, round 1, item 2).**
An earlier revision also overrode `has_permission()` as a view-level pre-check: deny early if the requester has no vendor profile at all, before DRF fetches the object. Re-evaluated directly against the two questions review raised:

1. *Does it provide meaningful defense-in-depth?* Only marginally — it saves one `get_object()` fetch for a requester who was always going to be denied by `has_object_permission` anyway. It changes no security outcome.
2. *Does it duplicate another permission class's responsibility?* Yes, structurally. Architecture §8 states permission classes are *"composed (not reimplemented) per view."* A view using `IsOwnerVendor` for an update/delete action will, in practice, already compose it with `IsAuthenticatedCustomer` and/or `IsVerifiedVendor` for coarser-grained gating — so re-checking authentication and vendor-profile existence inside `IsOwnerVendor` duplicated logic that composition already provides, inside a class the architecture explicitly scopes to object-level ownership only.

Given a marginal, non-security benefit and confirmed structural duplication, the override was **removed**. `IsOwnerVendor` now relies solely on `has_object_permission`; DRF's inherited `BasePermission.has_permission` (unconditionally `True`) is used unmodified. This is locked in by a dedicated test (`test_has_permission_is_not_overridden`) asserting `IsOwnerVendor.has_permission is BasePermission.has_permission`, so a future edit that silently reintroduces a pre-check will fail the suite rather than pass unnoticed. Views remain responsible for composing `IsOwnerVendor` alongside `IsAuthenticatedCustomer`/`IsVerifiedVendor` wherever coarser-grained gating is also needed, exactly as Architecture §8 already prescribes for every permission class.

**`_resolve_vendor_profile` extensibility (CTO review, round 1, item 4 — documentation only, no logic change).** The resolver is written as a sequence of independent `getattr(...)` probes rather than a single hardcoded path, specifically so a future vendor-owned model shape introduced later in the build order can be supported by adding one more probe, without redesigning `IsOwnerVendor`'s public interface. This mirrors the "configured, not subclassed-and-modified" philosophy already established for `common`'s mixins (`common` EDD §13) and this app's own `ActiveUniversityFilterBackend` lookup-field configuration (§6).

**Classification: Explicit Requirement** (Architecture §8) — object-level ownership check only; no additional view-level behavior.

### 5.4 `IsAdmin`

Architecture §8, verbatim: *"IsAdmin — is_staff/is_superuser."*

DDS §4.2 explicitly distinguishes `User.is_staff` ("Django admin-site access only, not the platform 'Admin' role") from the platform Admin role described in PRD §4. `IsAdmin` *is* that platform-role check — Architecture §8 states role state is *"computed from relations, not stored as a redundant field"*, and this class implements exactly that: it reuses Django's own `is_staff`/`is_superuser` fields rather than introducing a redundant, driftable role column.

**Classification: Explicit Requirement** (Architecture §8).

---

## 6. Filter Backend

### `ActiveUniversityFilterBackend` (`filters.py`)

Narrows a queryset to rows belonging to the requesting user's `active_university` (DDS §4.2). Explicit Requirement — Architecture §1 names the file and class directly; DDS §7.3 names it as the mechanism enforcing "strict university scoping" for all product browse/search queries.

**Configuration.** The filtered field name defaults to `"university"` (matching `Product.university`, DDS §4.7 — currently the only model documented as requiring this scoping), but is overridable per-view via a `university_lookup_field` attribute, so a future university-scoped model does not require a `core` code change. **Classification: Engineering Implementation Decision**, following the same "configured, not subclassed-and-modified" philosophy already established for `common`'s mixins/fields (`common` EDD §13).

**Behavior on missing scoping context.** Neither the PRD, Architecture, nor DDS specifies what should happen when there is no university to scope by. Two cases are handled identically, by returning an **empty queryset**:

1. The request is unauthenticated.
2. The request is authenticated but `active_university` is `None` (DDS §4.2: nullable "until onboarding completes").

**CTO review, round 1, item 3** asked this to be compared explicitly against `PermissionDenied` and `ValidationError`. Both were re-considered and rejected; empty queryset is retained. The full reasoning is documented in `filters.py`'s docstring — summarized here:

- **`PermissionDenied` rejected:** a missing `active_university` is not an authorization failure — the requester may be fully entitled to browse once onboarding completes. Raising it from `filters.py` would also mean a *filter backend* is making an *authorization* decision, blurring the boundary Architecture §1/§2 draws deliberately between `core/permissions.py` (authorization) and `core/filters.py` (query narrowing).
- **`ValidationError` rejected:** nothing about the request itself is malformed — the problem is a property of the user's onboarding state, not the input. Raising it here would also introduce a new pattern this codebase doesn't otherwise use: per Architecture §7 and the `common` EDD §9, exceptions are raised from service layers and serializers, not filter backends.
- **Empty queryset retained** because: (a) it cannot leak data — the only alternative that's safe by construction; (b) it keeps `core`'s own permissions/filters boundary intact, and matches how every other DRF filter backend behaves (narrow silently, never raise); (c) it requires no bespoke exception handling in every consuming view for what is really a "nothing to show yet" state; (d) steering an unonboarded user away from a browse endpoint is a client-flow / future-`users`-app responsibility, not something a `core` filter backend should take on.

This is documented as **reviewed-and-retained**, not a silent assumption — see §9.

**Classification: Engineering Implementation Decision** (re-evaluated and retained, CTO review round 1, item 3).

---

## 7. Why This App Has No Models, Migrations, Serializers, Views, URLs, Admin, or Services

The task brief for this app asks for "all files required for a production-ready application... where applicable." For `core`, several of those categories are **not applicable**, and are omitted deliberately rather than by oversight:

| Category | Included? | Reasoning |
|---|---|---|
| `models.py` / `migrations/` | No | Architecture §2: `core`'s "Does NOT own" column reads "Models, migrations," verbatim. `core` persists nothing. |
| `serializers.py` | No | `core` is not API-facing; it produces no request/response shapes of its own. |
| `views.py` / `urls.py` | No | `core` is consumed *by* other apps' views (as permission classes / filter backends); it exposes no endpoints of its own. Architecture §1's file tree for `core` lists only `permissions.py` and `filters.py`. |
| `admin.py` | No | No models exist to register with the Django admin site. |
| `services.py` | No | Architecture §7 defines the service layer as owning *mutating business logic per domain app*. `core`'s permission/filter logic is request-time access control and query scoping, not a business operation with side effects — there is nothing here that needs a transaction boundary or a domain-specific exception. Nothing in the frozen documents implies `core` needs one. |
| `apps.py` | Yes | Included for structural consistency with every other app (mirrors `common`'s `apps.py`, which exists despite `common` also owning no concrete models) and to allow `core` to be added to `INSTALLED_APPS` if a future, currently unforeseen need (e.g. a Django system check) requires the app registry. Not functionally required today. |
| `tests/` | Yes | Full coverage of both files — see §8. |
| Documentation | Yes | This document. |

This mirrors the `common` app EDD's own precedent exactly: `common` also omits `serializers.py` (removed during CTO review, ADR-003) and needed no `views.py`/`urls.py`/`admin.py` (beyond a thin, model-agnostic `SoftDeleteAdminMixin`) because those categories genuinely did not apply to what `common` is.

---

## 8. Testing Strategy and Coverage

**Approach.** `django.test.SimpleTestCase` is used throughout — no database access is required, since every permission/filter check operates purely on attributes of `request.user`/`view`/`obj`, never on a real queryset execution.

**Test-double rationale — forward app dependency.** `core` is implemented before `users`, `vendors`, and `stores` exist in the confirmed build order. Rather than importing real domain models that don't exist yet, tests use `types.SimpleNamespace` (for permission tests) and `unittest.mock.MagicMock` (for the filter backend's queryset) that expose *exactly* the documented attributes each class relies on (`user.is_authenticated`, `vendor_profile.is_verified`, `obj.store.vendor_profile`, `queryset.filter()`/`queryset.none()`). This keeps the suite fully independent of build order today, while exercising the exact interface contract those future apps must satisfy — no test will need to change once `users`/`vendors`/`stores` are implemented; the `SimpleNamespace` doubles will simply be replaceable by real model instances exposing the same attributes.

**Verified results, round 2 (post CTO-review revisions):**
- 28 tests, all passing (3 removed with the `has_permission` override; 3 added — a design-lock-in test, a behavioral confirmation test, and a pk-only equality test exercising the `==` comparison change — net count unchanged).
- 100% line coverage of `permissions.py` (43 statements, down from 46 after removing `has_permission`), `filters.py`, and `apps.py`.
- Clean `flake8` run (`--max-line-length=100`) across **both** source and test files — round 1 review prompted linting the `tests/` directory for the first time, which surfaced and fixed one pre-existing `F841` (unused variable) finding in `test_filters.py`.
- All five importable symbols import cleanly under a bare-minimum Django settings module with **zero domain apps installed** — unchanged, re-verified.

Actual terminal output for all four checks is reproduced in full in §10 (Self-Review), per CTO review item 5's request that future submissions include real output rather than reported summaries.

**Coverage by file:**

| Test file | What it covers |
|---|---|
| `test_permissions.py` | All four permission classes: authenticated/anonymous/missing-user paths; verified/unverified/suspended-shaped/no-profile vendor paths; matching/mismatched/unrecognized-shape/client-supplied-identifier-attack object-ownership paths; staff/superuser/regular-customer/anonymous-with-stale-flag admin paths. |
| `test_filters.py` | Authenticated-with-university (default and overridden lookup field), anonymous, no-active-university, and missing-user-on-request paths; confirms `.filter()` is called with the exact expected kwarg and `.none()`/`.filter()` are mutually exclusive per case. |

**Known limitation, recorded for the record (mirrors the `common` EDD's own §16 disclosure format):** verification above was run against Django 6.0.7 / DRF 3.17.1 — the latest versions available via `pip` at implementation time — rather than pinned Django 5.x, since the project's dependency pins (`requirements.txt`) have not yet been established as of this app. The permission/filter code uses only stable, long-standing DRF APIs (`BasePermission`, `BaseFilterBackend`) unchanged across this range, so no compatibility risk is expected, but re-running the suite once the project's actual `requirements.txt` is pinned is recommended before merging.

---

## 9. Assumptions Flagged for CTO Review

Following the same practice as DDS §13 ("Assumptions"):

1. **`ActiveUniversityFilterBackend` returns an empty queryset (not an error, and not the unfiltered queryset) when the requester has no `active_university`** (unauthenticated, or authenticated but pre-onboarding). No frozen document specifies this edge case. **Reviewed against `PermissionDenied` and `ValidationError` in CTO review round 1 (item 3) and retained** — see §6 for the full comparison. If product intent later differs (e.g., a distinct "please select a university" signal is preferred over a silently empty list), the filter backend would need a revision, and the owning view/viewset would need to communicate that state to the client — but this is no longer an unreviewed assumption, it is a reviewed-and-confirmed default.
2. **`core` is not currently listed in any `INSTALLED_APPS`** in this deliverable, since no real project `settings.py` exists yet in the build order. `apps.py`/`CoreConfig` is provided in anticipation of that, but the actual settings wiring is deferred to whichever future step establishes `config/settings/`.
3. **`IsOwnerVendor`'s `_resolve_vendor_profile` helper currently recognizes exactly two object shapes** (`Store` and `Product`, per DDS §4.5/§4.7). If a future domain app introduces another vendor-owned, ownership-checkable object shape, this helper will need a corresponding branch — flagged here so it isn't discovered by surprise later in the build order. The helper's docstring was expanded in CTO review round 1 (item 4) to state this extensibility explicitly; no logic changed.

---

## 10. Self-Review (Technical)

Performed before resubmitting, per the project's stated "perform a technical self-review before finishing" requirement, and expanded per CTO review item 5 to include actual terminal output rather than reported summaries.

- [x] Every class name and file matches Architecture §1 and §8 verbatim — no invented permissions, no invented filters.
- [x] No model, migration, enum, or business rule was introduced anywhere in this app — verified by grep-level inspection (no `models.Model`, no `import` of any domain app) and by the zero-domain-apps import test below.
- [x] `IsOwnerVendor` never reads a vendor/store identifier from `request.data`, `request.query_params`, or `view.kwargs` — verified by reading the implementation and by the dedicated `test_object_level_ignores_client_supplied_identifiers` test.
- [x] `IsOwnerVendor` compares ownership via Django-model-style equality (`==`), not manual `.pk` access — verified by grep (no `.pk ==` remains) and by `test_object_level_treats_same_pk_as_same_owner_regardless_of_other_fields`.
- [x] `IsOwnerVendor.has_permission` is confirmed to be DRF's own inherited method, not a class-specific override — verified by `test_has_permission_is_not_overridden` (`assertIs` against `BasePermission.has_permission`).
- [x] All four permission classes and the filter backend handle `request.user` being `None` or unauthenticated without raising — verified by dedicated tests for each class.
- [x] No signals used anywhere in this app — not applicable regardless, since `core` has no models to attach signals to.
- [x] No `transaction.atomic()` needed — `core` performs no multi-model writes.
- [x] Confirmed zero import-time coupling to any domain app by successfully importing every `core` symbol under a settings module with only `rest_framework` installed.

### 10.1 Terminal output — test run

```
$ DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=. python -m django test apps.core.tests -v 2
Found 28 test(s).
Skipping setup of unused database(s): default.
System check identified no issues (0 silenced).
test_anonymous_user_gets_empty_queryset ... ok
test_authenticated_user_with_active_university_filters_by_it ... ok
test_default_lookup_field_is_university ... ok
test_missing_user_on_request_gets_empty_queryset ... ok
test_user_without_active_university_gets_empty_queryset ... ok
test_view_can_override_lookup_field ... ok
test_anonymous_staff_flag_is_denied ... ok
test_missing_user_on_request_is_denied ... ok
test_regular_customer_is_denied ... ok
test_staff_user_is_allowed ... ok
test_superuser_is_allowed ... ok
test_anonymous_user_is_denied (IsAuthenticatedCustomerTests) ... ok
test_authenticated_user_is_allowed ... ok
test_missing_user_on_request_is_denied (IsAuthenticatedCustomerTests) ... ok
test_has_permission_default_is_unconditionally_true ... ok
test_has_permission_is_not_overridden ... ok
test_object_level_allows_matching_product_owner_via_store ... ok
test_object_level_allows_matching_store_owner ... ok
test_object_level_denies_anonymous_user ... ok
test_object_level_denies_different_vendor ... ok
test_object_level_denies_unrecognized_object_shape ... ok
test_object_level_denies_when_requester_has_no_vendor_profile ... ok
test_object_level_ignores_client_supplied_identifiers ... ok
test_object_level_treats_same_pk_as_same_owner_regardless_of_other_fields ... ok
test_anonymous_user_is_denied (IsVerifiedVendorTests) ... ok
test_customer_with_no_vendor_profile_is_denied ... ok
test_unverified_or_suspended_vendor_is_denied ... ok
test_verified_vendor_is_allowed ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.004s

OK
```

### 10.2 Terminal output — coverage

```
$ DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=. coverage run --source=apps.core \
    --omit="apps/core/tests/*" -m django test apps.core.tests
Ran 28 tests in 0.007s

OK

$ coverage report -m
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
apps/core/__init__.py          0      0   100%
apps/core/apps.py              5      0   100%
apps/core/filters.py          12      0   100%
apps/core/permissions.py      43      0   100%
--------------------------------------------------------
TOTAL                         60      0   100%
```

### 10.3 Terminal output — lint

```
$ flake8 --max-line-length=100 apps/core/permissions.py apps/core/filters.py apps/core/apps.py \
    apps/core/tests/test_permissions.py apps/core/tests/test_filters.py
$ echo "exit code: $?"
exit code: 0
```

(One `F841` unused-variable finding in `test_filters.py` was caught and fixed as part of this round — see Revision History, item 5.)

### 10.4 Terminal output — zero domain-app coupling proof

```
$ python -c "
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['rest_framework'], DEFAULT_AUTO_FIELD='django.db.models.BigAutoField')
django.setup()
from apps.core.permissions import IsAuthenticatedCustomer, IsVerifiedVendor, IsOwnerVendor, IsAdmin
from apps.core.filters import ActiveUniversityFilterBackend
print('All core symbols import cleanly with a bare-minimum settings module (no domain apps installed).')
"
All core symbols import cleanly with a bare-minimum settings module (no domain apps installed).
```

**Outcome:** `core` has been revised per CTO review round 1 and is ready for sign-off. No further product or architectural questions arose during revision — all three retained/re-evaluated items in §9 are edge-case *engineering* defaults, explicitly reviewed, not ambiguities in the frozen PRD/Architecture/DDS themselves.

---

## 11. Summary

`core` is complete and has been revised per CTO review, round 1. It consists of 3 implementation files (`apps.py`, `permissions.py`, `filters.py`), one usage document (this README), and 2 test files — 6 files total (plus `__init__.py`s), owning zero concrete database tables and zero API endpoints of its own. It supplies:

- `IsAuthenticatedCustomer`, `IsVerifiedVendor`, `IsOwnerVendor`, `IsAdmin` — the four permission classes named directly by Architecture §8, each implemented via attribute access against documented model interfaces rather than direct imports of domain models that do not yet exist in the build order. `IsOwnerVendor` now compares ownership via Django-model-style `==` and relies solely on `has_object_permission` (no view-level pre-check), per review.
- `ActiveUniversityFilterBackend` — the single shared enforcement point for strict university scoping, named directly by Architecture §1 and DDS §7.3, with a configurable lookup field and an empty-queryset default for the missing-scoping-context edge case, now documented with an explicit, reviewed comparison against `PermissionDenied` and `ValidationError`.

One reviewed-and-retained engineering default (the empty-queryset behavior in `ActiveUniversityFilterBackend`) and one structural note (`INSTALLED_APPS` wiring deferred to the real settings module) remain noted in §9, but neither is an open question — both were explicitly evaluated during review. `core` does not block progression to the next application in the build order (`universities`).
