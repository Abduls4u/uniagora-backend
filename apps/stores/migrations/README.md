# Stores

The `stores` app owns the public-facing storefront profile for verified UniAGORA vendors.

It is intentionally separated from the `vendors` app: `vendors` owns vendor identity, verification, and supporting documents, while `stores` owns the storefront presentation exposed to customers. This separation reflects the approved Backend Architecture and Database Design Specification.

## Responsibility

The app manages:

* Store creation for verified vendors
* Public storefront retrieval
* Vendor-owned storefront retrieval and editing
* Store soft deletion
* Store active/inactive state
* Store slug-based public lookup

The app does **not** own:

* Vendor verification or vendor identity
* Vendor documents
* Products
* Categories
* Reviews
* Vendor suspension decisions

`Store` lifecycle state is coordinated with the vendor lifecycle through the vendor service layer. The Database Design Specification explicitly assigns `Store` profile edits to `StoreService`, while `is_active` is controlled by `VendorSuspensionService`.

## Model

The app currently owns one model:

### `Store`

A `Store` has a one-to-one relationship with `VendorProfile`.

| Field            | Purpose                                   |
| ---------------- | ----------------------------------------- |
| `vendor_profile` | Owning vendor                             |
| `display_name`   | Public storefront name                    |
| `slug`           | Unique public storefront identifier       |
| `description`    | Optional storefront description           |
| `contact_phone`  | Optional storefront contact number        |
| `is_active`      | Whether the storefront is publicly active |

The approved schema defines `vendor_profile` as one-to-one and `slug` as globally unique. `description` and `contact_phone` are optional fields.

## API

All endpoints are under `/api/v1/`.

| Method   | Endpoint          | Access                 | Purpose                                     |
| -------- | ----------------- | ---------------------- | ------------------------------------------- |
| `POST`   | `/stores/`        | Verified Vendor        | Create a store                              |
| `GET`    | `/stores/{slug}/` | Authenticated Customer | Retrieve an active public store             |
| `GET`    | `/stores/me/`     | Authenticated Customer | Retrieve the authenticated user's own store |
| `PATCH`  | `/stores/me/`     | Authenticated Customer | Update the authenticated user's store       |
| `DELETE` | `/stores/me/`     | Authenticated Customer | Soft-delete the authenticated user's store  |

There is intentionally **no collection `GET /stores/` action**. Public storefront retrieval is performed through the slug-based detail endpoint.

## Service Layer

Business logic is centralized in `StoreService`.

Views remain thin and delegate mutations to services, following the project's service-layer convention. Services own transaction boundaries and domain rules rather than placing business logic in views or serializers.

Store lifecycle coordination also integrates with:

* `VendorSuspensionService` — controls storefront active state during vendor suspension/reinstatement
* `Product` lifecycle — future product suspension/reinstatement cascades will integrate through the appropriate product services

The architecture explicitly requires `Store.is_active` to be maintained by the vendor suspension workflow rather than directly by vendors.

## Authorization

Store ownership is derived from the authenticated user's `VendorProfile`.

Client-supplied vendor/store identifiers are not trusted for ownership decisions. This follows the project's authorization rule that vendor-owned resources must derive ownership from the authenticated user rather than request-body identifiers.

### Access rules

* Only verified vendors can create stores.
* Authenticated users can retrieve public active stores.
* A vendor can access and modify only their own store through `/stores/me/`.
* Inactive or soft-deleted stores are not publicly retrievable.
* Store suspension/reactivation is controlled by vendor lifecycle services.

## Response Contract

The app uses the shared response envelope defined by `apps.common.response`.

### Success

```json
{
  "success": true,
  "message": "",
  "data": {}
}
```

### Failure

```json
{
  "success": false,
  "message": "",
  "errors": {}
}
```

This keeps the Stores API consistent with the project's global API contract.

## Data Integrity

Key invariants include:

* One store per vendor.
* Store slug is unique.
* Store ownership is tied to `VendorProfile`.
* Store deletion uses the project's soft-delete mechanism.
* Store active state reflects vendor suspension/reinstatement.
* Store records do not own vendor verification data.

The `Store → VendorProfile` relationship uses `CASCADE` because a store has no independent meaning without its vendor profile.

## Testing

The Stores implementation has been quality-gated against the project's full test suite.

Current verification:

```text
293 tests
293 passed
0 failures
0 errors
```

Django system checks also complete successfully.
