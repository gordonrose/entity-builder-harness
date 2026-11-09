import type { Clock } from "./contracts";

export const systemClock: Clock = {
  now: () => new Date(),
};

export function fixedClock(now: Date): Clock {
  return {
    now: () => new Date(now.getTime()),
  };
}
