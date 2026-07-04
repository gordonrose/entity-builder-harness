export type SecretString = string & { readonly __brand: "SecretString" };

export interface Hash {
  readonly algorithm: string;
  readonly value: string;
}

export interface Hasher {
  hash(value: SecretString): Promise<Hash>;
  verify(value: SecretString, expected: Hash): Promise<boolean>;
}

export interface PolicyViolation {
  readonly code: string;
  readonly message: string;
}
