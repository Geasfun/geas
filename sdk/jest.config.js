/** @type {import("jest").Config} */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  testMatch: ["**/tests/**/*.test.ts"],
  transform: {
    "^.+\\.ts$": ["ts-jest", { tsconfig: { strict: false } }],
  },
  collectCoverageFrom: ["src/**/*.ts", "!src/**/*.d.ts"],
};
