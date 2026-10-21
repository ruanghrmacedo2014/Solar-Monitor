from app.models.user_tenant import TenantRole


CUSTOMER_CREATE_ROLES = {
    TenantRole.TENANT_ADMIN,
    TenantRole.OPERATOR,
}

USER_TENANT_MANAGE_ROLES = {
    TenantRole.TENANT_ADMIN,
}

USER_CREATE_ROLES = {
    TenantRole.TENANT_ADMIN,
}