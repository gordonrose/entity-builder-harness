import { createCognitoAccessTokenVerifier, createCognitoJwtBearerAuthenticationHookFromEnv, type CognitoAccessTokenVerifierOptions } from "../src/index";
import type { PlatformJwtVerifier } from "@kanbien/platform-security";
declare const options: CognitoAccessTokenVerifierOptions;
const verifier: PlatformJwtVerifier = createCognitoAccessTokenVerifier(options);
const loaded = createCognitoJwtBearerAuthenticationHookFromEnv({});
if (!loaded.ok) { const code: "PLATFORM_ADAPTER_AWS_COGNITO_CONFIG_INVALID" = loaded.error.code; void code; }
void verifier;
