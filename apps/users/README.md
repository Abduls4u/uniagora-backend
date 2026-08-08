# UniAGORA Users App

The `users` app owns the canonical identity record for every UniAGORA account.

It contains the project's custom Django `User` model and the identity-level behavior associated with that model, including the user's email identity, profile information, account state, and active university selection.

The app is deliberately separate from `authentication`.

Where `authentication` answers **how an account authenticates**, `users` answers **who the account is**.

---

## 1. Responsibility

The Users app owns:

* The custom `User` model
* User identity
* Email-based authentication identity
* Password storage through Django's authentication framework
* User profile fields
* Active university selection
* Account activation/deactivation state
* User model manager behavior
* User serialization
* User-level identity validation

The app does **not** own:

* Registration workflow
* Login workflow
* JWT issuance
* Logout/token blacklisting
* Password-reset workflow
* Vendor profile data
* Store data
* Product data
* University management
* Marketplace business rules

The architectural boundary is:

```text
users
  ├── owns User
  │
  ├── depends on common
  │
  └── references universities
```

---

## 2. Identity Model

UniAGORA uses a custom Django User model.

The architecture specifies:

```text
AbstractBaseUser
        +
PermissionsMixin
        +
BaseModel
```

The User model uses:

```text
email
```

as `USERNAME_FIELD`.

This allows UniAGORA authentication to use email rather than Django's traditional username field.

The model uses the project's UUID-based identity convention inherited from `common.BaseModel`.

---

## 3. User as the Canonical Account

There is exactly one account identity per email.

The PRD explicitly establishes:

> One account per email.

The database therefore enforces email uniqueness.

Email values are normalized to lowercase before persistence/authentication-related lookup so that casing does not create multiple logical accounts.

Example:

```text
User@example.com
user@example.com
USER@EXAMPLE.COM
```

must resolve to the same logical email identity.

---

## 4. User Fields

The User model is defined around the following identity/profile information.

| Field               | Purpose                                                       |
| ------------------- | ------------------------------------------------------------- |
| `id`                | UUID primary key inherited from `BaseModel`                   |
| `email`             | Unique account/authentication identifier                      |
| `password`          | Django-managed hashed password                                |
| `full_name`         | User's display name                                           |
| `phone_number`      | Optional validated phone number                               |
| `active_university` | User's currently selected university                          |
| `is_active`         | Django account enabled/disabled state                         |
| `is_staff`          | Django administrative/staff capability                        |
| `date_joined`       | Account creation timestamp used for Django auth compatibility |
| `created_at`        | Common model creation timestamp                               |
| `updated_at`        | Common model update timestamp                                 |
| `is_deleted`        | Common soft-deletion flag                                     |

The exact field implementation remains governed by the DDS and current model code.

---

## 5. UUID Identity

User records use UUID primary keys through the shared `BaseModel` convention.

This means application code should not assume integer user IDs.

For example:

```text
user.id
```

is a UUID rather than an auto-incrementing integer.

This convention is shared across the project's persisted domain entities.

---

## 6. Email Identity

Email is the canonical login identifier.

The model enforces uniqueness at the database level.

The system also normalizes email values to lowercase.

The database constraint is important because application-level duplicate checks alone are insufficient to guarantee uniqueness under concurrent requests.

The Users app therefore treats the database uniqueness constraint as the final integrity boundary.

---

## 7. Password Handling

The Users model delegates password security to Django's authentication system.

Passwords must never be stored as plaintext.

Password creation and replacement should use Django's standard APIs, such as:

```python
user.set_password(...)
```

or the project's user manager:

```python
User.objects.create_user(...)
```

Authentication workflows are owned by `authentication`, but the User model remains the underlying Django authentication identity.

---

## 8. User Manager

The custom User manager is responsible for creating users through the correct Django authentication APIs.

The manager provides the expected creation path:

```text
User.objects.create_user(...)
```

This ensures:

* Password hashing
* Email-based identity
* Required User fields
* Consistent account creation behavior

Code should not bypass the manager with direct low-level creation when creating normal user accounts.

Administrative/superuser creation should likewise use the manager's appropriate Django-compatible path.

---

## 9. Active University

A User may have an `active_university`.

The relationship is conceptually:

```text
University
     │
     └──< User.active_university
```

The field is nullable because university selection may not yet have been completed.

The product decision allows users to change their active university.

The active university is particularly important because UniAGORA uses university-scoped marketplace behavior.

The architecture establishes university scoping as a cross-cutting concern rather than duplicating the rule throughout individual domain views.

---

## 10. University Scoping

The Users app owns the user's selected university.

It does **not** own the global university-scoping mechanism.

The cross-cutting `ActiveUniversityFilterBackend` belongs to `core`.

Conceptually:

```text
User.active_university
          ↓
core.ActiveUniversityFilterBackend
          ↓
University-scoped domain queries
```

This distinction prevents the User model from becoming responsible for marketplace filtering logic.

---

## 11. Role Architecture

UniAGORA does not use a collection of redundant role flags on the User model.

The architecture deliberately avoids fields such as:

```text
is_vendor
is_customer
is_admin
```

as independent sources of truth.

Instead:

### Customer

Every authenticated account begins as a Customer.

The PRD establishes that Vendors retain Customer permissions.

### Vendor

Vendor identity is established by the existence/state of the related `VendorProfile`.

The relationship is:

```text
User
 │
 └── 1:1 ── VendorProfile
```

The Users app does not own vendor verification or vendor lifecycle.

### Admin

Administrative access is determined through the platform's administrative authorization mechanism, including Django's staff/superuser capabilities as defined by the architecture.

The Users app does not implement admin business workflows.

---

## 12. Vendor Boundary

The Users app deliberately does not contain fields such as:

```text
vendor_status
matric_number
store_name
verification_status
vendor_type
```

Those belong to the vendor domain.

The architectural relationship is:

```text
User
 │
 └── 1:1
       ↓
VendorProfile
       │
       └── 1:1
             ↓
           Store
```

This separation prevents the User model from becoming a large collection of marketplace-specific concerns.

---

## 13. Account Lifecycle

The User lifecycle is intentionally simple in MVP.

Conceptually:

```text
Account created
      ↓
active
      │
      └── administrative/service action
                  ↓
              inactive
```

The DDS specifies that users are not hard-deleted as part of the MVP account lifecycle.

Deactivation is represented using:

```text
is_active = False
```

rather than destroying the account record.

This preserves historical relationships such as:

* Conversations
* Reports
* Vendor history
* Notifications
* Other domain records referencing the user

---

## 14. Soft Deletion

User records inherit the project's common soft-deletion mechanism.

The existence of `is_deleted` must not be confused with authentication disablement.

Conceptually:

```text
is_active
    ↓
Can this account authenticate?

is_deleted
    ↓
Has this record been soft-deleted at the common persistence layer?
```

Application workflows must respect the semantics established by `common`.

User history should not be casually destroyed.

---

## 15. University Relationship Integrity

The DDS specifies that:

```text
User.active_university → University
```

uses a protected relationship.

The purpose is to prevent deleting a university out from under users who reference it.

Universities should instead be deactivated when they should no longer be available for normal selection.

This aligns with the broader platform rule that inactive universities remain in the database while being hidden from normal active-user flows.

---

## 16. Serialization

The Users app owns user serialization.

The User serializer is consumed by other API boundaries, including authentication responses.

The serializer should expose only information appropriate for the consuming client.

Sensitive authentication data, especially the password hash, must never be serialized.

The serializer is responsible for representation and input validation; cross-model business workflows belong in services.

---

## 17. Validation

User-level validation includes:

### Email

* Valid email format
* Lowercase normalization
* Uniqueness

### Full name

* Required
* Maximum length according to the model contract

### Phone number

* Optional
* Validated using the shared phone-number validator
* Stored consistently with the model's non-null persistence contract

### Active university

* May be absent until onboarding is complete
* Must reference a valid University
* University selection/change behavior belongs to the appropriate user service boundary

---

## 18. Service Layer

The architecture separates domain workflows from model methods.

User workflows that involve business rules should be handled through a user service rather than embedding multi-step business behavior inside the User model.

The DDS identifies the User ownership boundary as including:

```text
UserService
AuthService
```

with:

```text
AuthService
    → registration / credentials

UserService
    → user-level operations
    → active university selection
```

This keeps authentication concerns and profile/domain concerns separated.

---

## 19. Dependencies

The Users app depends primarily on:

```text
users
  ├── common
  └── universities
```

It must remain independent of later marketplace applications wherever possible.

The User model may be referenced by:

```text
vendors
stores
chat
reviews
reports
notifications
```

but those applications should not force marketplace-specific fields or workflows into the User model.

---

## 20. Domain Relationships

The principal User relationships are:

```text
University
    │
    └──< User
            │
            ├── 1:1 → VendorProfile
            │            │
            │            └── 1:1 → Store
            │
            ├── 1:N → Conversations
            ├── 1:N → Reports
            ├── 1:N → Notifications
            └── 1:N → DeviceTokens
```

The User is therefore a foundational entity referenced by many domain applications.

Changes to its identity contract should be treated as high-impact changes.

---

## 21. API Responsibility

The Users app owns user identity/profile behavior, while the authentication app owns authentication workflows.

The backend responsibility specification identifies user-facing API responsibilities including:

* Register
* Login
* Profile
* Update Profile

The exact endpoint ownership must follow the frozen architecture and current implementation rather than duplicating authentication endpoints inside the Users app.

Authentication endpoints remain under `authentication`.

User/profile operations belong to the Users boundary.

---

## 22. Security Considerations

The User model is one of the most security-sensitive models in the system.

The app must preserve:

* Unique email identity
* Secure password hashing
* Input validation
* Proper authentication-manager usage
* Permission-aware profile changes
* Protection of sensitive fields
* No client-controlled administrative elevation
* No client-controlled vendor-role elevation
* Database-level uniqueness enforcement

A client must never be able to submit something equivalent to:

```json
{
    "is_staff": true
}
```

and gain administrative capability.

Likewise, vendor identity must not be created by simply submitting an arbitrary role field.

Role transitions belong to their respective domain workflows.

---

## 23. Testing Expectations

The Users app should test:

### Model

* User creation
* Email uniqueness
* Email normalization
* Password hashing
* User string representation
* Active university relationship
* Account activation/deactivation
* UUID identity

### Manager

* `create_user()`
* Required fields
* Password hashing
* Email normalization
* Invalid creation scenarios
* Superuser creation behavior

### Serialization

* Valid user representation
* Sensitive-field exclusion
* Phone-number validation
* Profile validation

### Service behavior

* Active-university changes
* User lifecycle operations
* Permission boundaries
* Relevant cross-domain invariants

### Integration

The complete project test suite should be run because User is a foundational model consumed by multiple applications.

---

## 24. Compatibility With Authentication

The relationship between the two apps should remain:

```text
             ┌─────────────────────┐
             │   authentication    │
             │                     │
             │ Register            │
             │ Login               │
             │ Logout              │
             │ JWT                 │
             │ Password Reset      │
             └──────────┬──────────┘
                        │
                        ↓
             ┌─────────────────────┐
             │       users         │
             │                     │
             │ User model          │
             │ User manager        │
             │ Profile identity    │
             │ University selection│
             └─────────────────────┘
```

Authentication may create or authenticate Users.

Users must not become responsible for JWT issuance or authentication endpoint orchestration.

---

## 25. What Does Not Belong Here

Do not add the following to the Users app merely because they involve users:

### Vendor functionality

Belongs to `vendors`:

* Vendor application
* Vendor verification
* Matric-number verification
* Vendor suspension
* Vendor documents

### Store functionality

Belongs to `stores`:

* Store profile
* Store slug
* Store description
* Store activation state

### Marketplace functionality

Belongs to the relevant domain apps:

* Products
* Categories
* Search
* Reviews
* Reports
* Chat
* Notifications

### Authentication functionality

Belongs to `authentication`:

* JWT issuance
* Logout
* Password-reset workflows
* Login endpoints
* Registration orchestration

This boundary is intentional and should be preserved.

---

## 26. Future Extensibility

The User model is a foundational entity.

Future changes should favor additive extensions over breaking changes.

Potential future capabilities should be introduced in their appropriate domain boundary rather than adding unrelated fields to `User`.

For example:

```text
Email verification
    → authentication

Vendor verification
    → vendors

Store profile
    → stores

Push device registration
    → notifications
```

The User model should remain focused on canonical account identity.

---

## 27. Definition of Done

The Users app is considered complete when:

* The custom User model is implemented.
* Email is the canonical authentication identifier.
* Email uniqueness is enforced.
* Passwords are securely hashed.
* User profile fields are validated.
* Active university selection is supported.
* Account state is correctly represented.
* Vendor/admin state is not redundantly stored as independent role flags.
* User serialization is safe.
* User services own appropriate user workflows.
* Database migrations are valid.
* Tests cover the User model and manager.
* Cross-app authentication integration works.
* Django system checks pass.
* The complete project test suite passes.

---
