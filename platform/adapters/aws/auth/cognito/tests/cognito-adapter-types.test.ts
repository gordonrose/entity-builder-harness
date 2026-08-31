import type { Permission } from "@kanbien/core/authz";
import {
  adapterMetadata,
  cognitoIssuer,
  createCognitoAccessTokenVerifier,
  createCognitoAuthzPermissionMapping,
  createCognitoJwtBearerAuthenticationHook,
  type CognitoAuthzPermissionMapping,
} from "../src/index";

const permission = "smoke:read" as Permission;
const authz: CognitoAuthzPermissionMapping = {
  groups: { administrators: [permission] },
  scopes: { "platform-smoke/read": [permission] },
};
void createCognitoAuthzPermissionMapping(authz);
void cognitoIssuer("eu-west-1", "eu-west-1_example");
void createCognitoAccessTokenVerifier({
  region: "eu-west-1",
  userPoolId: "eu-west-1_example",
  appClientId: "app-client",
});
void createCognitoJwtBearerAuthenticationHook({
  region: "eu-west-1",
  userPoolId: "eu-west-1_example",
  appClientId: "app-client",
  authz,
});
void adapterMetadata.provider;

const invalidAuthz: CognitoAuthzPermissionMapping = {
  groups: {
    // @ts-expect-error adapter mappings must grant core Permission values.
    administrators: [1],
  },
};
void invalidAuthz;
