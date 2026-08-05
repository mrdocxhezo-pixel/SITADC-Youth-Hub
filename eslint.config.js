import js from "@eslint/js";

export default [
    js.configs.recommended,
    {
        files: ["static/js/**/*.js"],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: "module",
            globals: {
                window: "readonly",
                document: "readonly",
                console: "readonly",
                bootstrap: "readonly",
                confirm: "readonly"
            }
        },
        rules: {
            "no-unused-vars": "warn",
            "no-undef": "error",
            "eqeqeq": "error"
        }
    }
];
