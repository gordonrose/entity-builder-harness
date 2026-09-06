import { deepEqual, equal } from "node:assert/strict";
import { createAlbTrustedClientAddressResolver } from "../src/index";

const resolver = createAlbTrustedClientAddressResolver({
  ingressMode: "alb-security-group-only",
});

equal(resolver.resolve({
  socketPeerAddress: "10.0.1.15",
  headers: { "x-forwarded-for": "198.51.100.20, 203.0.113.31" },
}), "203.0.113.31");

equal(resolver.resolve({
  socketPeerAddress: "10.0.1.15",
  headers: { "x-forwarded-for": "not-an-address" },
}), "10.0.1.15");

equal(resolver.resolve({
  socketPeerAddress: "10.0.1.15",
  headers: {},
}), "10.0.1.15");

deepEqual(
  resolver.resolve({
    socketPeerAddress: "10.0.1.15",
    headers: { "x-forwarded-for": ["198.51.100.20", "203.0.113.31"] },
  }),
  "198.51.100.20",
);

console.log("ECS Fargate trusted-ingress adapter runtime test passed.");
