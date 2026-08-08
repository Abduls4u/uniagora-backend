# UniAGORA Authentication App

The `authentication` app is the centralized authentication boundary for UniAGORA.

It provides the authentication workflows required by the MVP while deliberately keeping **identity data and persisted user state inside the `users` app**.

The app is intentionally **model-free**. JWT authentication is handled through SimpleJWT, while password-reset tokens use Django's signed-token mechanism rather than a dedicated persisted reset-token model.

This boundary follows the frozen Backend Architecture and DDS.

---

## 1. Responsibility

The authentication app owns:

* User registration
* User login
* JWT issuance
* Refresh-token handling through SimpleJWT
* Logout through refresh-token blacklisting
* Forgot-password flow
* Password-reset confirmation
* Authentication-specific input validation
* Authentication-specific service-layer workflows

The app does **not** own:

* The `User` model
* User profile data
* University assignment
* Vendor identity
* Vendor verification
* Roles as persisted data
* User lifecycle/profile management outside authentication
* Any authentication-specific persisted model

The architectural boundary is:

```text
authentication
      │
      └── depends on
             ↓
           users
```

The `authentication` app must not become a second owner of user data.

---

## 2. Product Scope

The MVP authentication requirements are:

1. Register
2. Login
3. Logout
4. Forgot Password
5. Password Reset

Authentication is centralized so the same backend authentication system serves:

* Web client
* Mobile client
* Admin client

Future authentication features identified by the PRD are:

* Email Verification
* Google Sign-In
* Apple Sign-In

These are intentionally not part of the current MVP implementation.

---

## 3. Architectural Position

The frozen architecture defines the application boundary as:

| App              | Owns                                                  |
| ---------------- | ----------------------------------------------------- |
| `authentication` | Register, login, logout, password reset, JWT issuance |
| `users`          | User model and active-university selection            |

This separation is important.

Authentication answers:

> "Can this account authenticate, and how do we issue/revoke authentication credentials?"

Users answers:

> "Who is this account, and what identity/profile information belongs to it?"

The authentication app should therefore remain thin and orchestration-focused.

---

## 4. Persistence

### No application-owned models

The authentication app intentionally has no domain models or migrations.

JWT issuance is stateless through `djangorestframework-simplejwt`.

Password reset uses Django's:

```text
PasswordResetTokenGenerator
```

rather than introducing a `PasswordResetToken` model.

Refresh-token blacklisting uses SimpleJWT's existing blacklist application rather than an authentication-owned token table.

This avoids duplicating authentication state and keeps the authentication boundary small.

---

## 5. Registration

Registration creates a `User` through the Users app's manager/service boundary.

The registration flow is conceptually:

```text
HTTP Request
     ↓
RegisterSerializer
     ↓
AuthService.register()
     ↓
User.objects.create_user()
     ↓
User
```

### Registration rules

* Email is required.
* Email is normalized before uniqueness validation.
* Password is write-only and validated through Django password validators.
* Full name is required.
* Phone number is optional.
* Every newly registered account is a Customer by default.
* Clients cannot submit arbitrary role/admin flags during registration.
* Account creation is performed transactionally.

The authentication app must never allow registration input to elevate an account into an administrative or vendor state.

Vendor status is established by the vendor domain workflow, while administrative access is controlled through the platform's admin authorization model.

---

## 6. Login

Login uses JWT authentication through SimpleJWT.

The User model uses:

```text
email
```

as its authentication identifier.

The login flow is:

```text
Credentials
    ↓
SimpleJWT
    ↓
User authentication
    ↓
Access token + refresh token
```

The authentication system is centralized across all clients.

Authentication configuration must therefore remain compatible with:

* Web
* Mobile
* Admin

No client should implement its own authentication mechanism.

---

## 7. JWT

JWT is the project's authentication mechanism.

SimpleJWT is responsible for:

* Credential authentication
* Access-token generation
* Refresh-token generation
* Token validation
* Token rotation/expiry according to project configuration
* Refresh-token blacklist integration

The authentication app should not implement a custom JWT system.

The architecture explicitly favors the existing SimpleJWT mechanism rather than introducing custom persisted authentication state.

---

## 8. Login Response

The login serializer extends SimpleJWT's token serializer and adds serialized user information to the token response.

Conceptually:

```json
{
    "access": "...",
    "refresh": "...",
    "user": {}
}
```

The exact response envelope and field structure must remain consistent with the project's API conventions.

Authentication response changes are API contract changes and should not be made casually because the same API is consumed by multiple clients.

---

## 9. Logout

Logout is implemented through refresh-token blacklisting.

The logout workflow is:

```text
Client
  ↓
Refresh token
  ↓
Validate token
  ↓
Verify token belongs to requesting user
  ↓
Blacklist token
```

### Security requirement

The requesting user must own the refresh token being blacklisted.

A valid refresh token belonging to another user must not be accepted merely because the token itself is structurally valid.

The implementation therefore:

1. Parses the refresh token.
2. Handles invalid/already-invalidated tokens.
3. Extracts the token's user identifier.
4. Compares it with the authenticated request user's ID.
5. Rejects ownership mismatches.
6. Blacklists the token only after ownership has been established.

This is an important security boundary.

---

## 10. Password Reset

Password reset is divided into two operations.

### 10.1 Forgot Password

The client submits an email address.

The service:

1. Normalizes the email.
2. Looks for an active user.
3. Silently does nothing when the account does not exist.
4. Generates a signed reset token when the account exists.
5. Builds the frontend reset URL.
6. Sends the reset email.

The endpoint intentionally does not reveal whether an email belongs to an account.

This prevents account enumeration.

Conceptually:

```text
POST forgot-password
        ↓
Look up active account
        ↓
Generate signed token
        ↓
Build reset URL
        ↓
Send email
```

Whether the email exists or not should produce the same externally observable success behavior.

---

### 10.2 Password Reset Confirmation

The client submits:

* UID
* Reset token
* New password

The service:

1. Decodes the UID.
2. Retrieves the user.
3. Validates the signed token.
4. Rejects invalid/expired tokens.
5. Sets the new password through Django's password hashing mechanism.
6. Saves the password transactionally.

No plaintext password is persisted.

---

## 11. Service Layer

Authentication business workflows belong in the service layer.

The architectural convention is:

```text
Views
  ↓
Serializers
  ↓
Services
  ↓
Domain models/managers
```

Services must not depend on views or serializers.

The service layer is responsible for transaction boundaries and business operations.

Current authentication service responsibilities include:

```text
AuthService.register()
AuthService.initiate_password_reset()
AuthService.confirm_password_reset()
```

JWT login is primarily delegated to SimpleJWT.

---

## 12. Validation

Authentication serializers own request-level validation.

Examples include:

* Email format
* Email normalization
* Duplicate-account detection
* Password validation
* Full-name validation
* Phone-number format validation
* Reset-token input validation

Business operations that involve persistence or side effects belong in services.

This separation keeps serializers focused on input/output validation rather than business workflows.

---

## 13. Error Handling

Authentication uses the project's shared exception system.

Expected business failures should be represented using the project's domain/common exceptions rather than implementing unrelated error-response structures inside authentication views.

The API contract is:

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

All authentication endpoints must preserve this contract.

---

## 14. Security Responsibilities

Authentication is a security-critical application.

It must preserve:

* Secure password hashing
* JWT-based authentication
* Password validation
* Token ownership verification during logout
* Password-reset token validation
* Account-enumeration resistance
* Input validation
* Authentication permission checks
* Consistent error handling

The authentication app must never:

* Store plaintext passwords
* Trust client-provided roles
* Accept arbitrary administrative flags during registration
* Blacklist another user's refresh token
* Reveal whether an email exists during password-reset initiation
* Bypass the User model's authentication manager

---

## 15. API Versioning

Authentication endpoints are exposed under the project's versioned API namespace:

```text
/api/v1/
```

Endpoint paths and response contracts are API agreements.

They must not be renamed or structurally changed without reviewing the frontend integration impact and obtaining the required technical approval.

The backend responsibility specification explicitly requires API documentation to remain synchronized with endpoint changes.

---

## 16. Dependencies

Primary dependencies:

```text
authentication
    ├── users
    ├── common
    ├── Django authentication/password utilities
    ├── Django REST Framework
    └── djangorestframework-simplejwt
```

The authentication app must not introduce dependencies on later domain apps such as:

* vendors
* stores
* products
* chat
* reviews
* notifications

unless an approved architectural requirement explicitly creates such a dependency.

---

## 17. Testing Expectations

Authentication tests must cover at minimum:

### Registration

* Successful registration
* Newly created account is active
* Customer-by-default behavior
* Duplicate email rejection
* Invalid email rejection
* Password validation
* Optional phone-number behavior
* User creation through the expected manager/service boundary

### Login

* Valid credentials
* Invalid credentials
* JWT issuance
* User payload in login response

### Logout

* Valid refresh-token blacklist
* Invalid token
* Already-invalidated token
* Token ownership mismatch

### Password Reset

* Existing active account
* Unknown email
* Reset-token generation
* Invalid token
* Expired token
* Invalid UID
* Successful password replacement
* Password hashing

### API behavior

* Authentication requirements
* Permission behavior
* Standard success envelope
* Standard error envelope

---

## 18. Future Extensions

The PRD identifies the following future authentication capabilities:

```text
Email Verification
Google Sign-In
Apple Sign-In
```

These should be added without violating the current app boundary.

In particular, future authentication features should not automatically justify creating new persisted authentication models. Any new persistence requirement should undergo architectural review first.

---

## 19. Out of Scope

The authentication app does not own:

* Vendor applications
* Vendor verification
* Store creation
* University management
* Product permissions
* Chat authorization
* Reviews
* Notifications
* Marketplace business rules
* Payment authentication
* Wallet authentication state
* Rider authentication workflows
* Any post-MVP feature not approved for this app

---

## 20. Definition of Done

Authentication is considered complete when:

* Registration works.
* Login works.
* Logout works.
* Password reset request works.
* Password reset confirmation works.
* JWT authentication is integrated.
* Refresh-token ownership is enforced during logout.
* Passwords are securely hashed.
* Password-reset enumeration is prevented.
* API responses follow the global response contract.
* Business logic is kept in the service layer.
* No authentication-owned persistence has been introduced.
* Tests cover the critical authentication paths.
* Django system checks pass.
* The complete project test suite passes.

---
