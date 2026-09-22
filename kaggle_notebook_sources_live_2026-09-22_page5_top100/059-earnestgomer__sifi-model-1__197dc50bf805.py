import kaggle_benchmarks as kbench
from kaggle_benchmarks import assertions, tools

@kbench.task(name="encrypt code for FGF-1 and FGF-2 and protein levels from NGL and FGL blood flow through ischemic vessels tissue")
def encrypt_biomarker_task(llm):
    # 1. Prompt the LLM to generate the code requested
    prompt = (
        "Develop a Python function that takes string inputs representing blood flow parameters "
        "and simulates the output levels for FGF-1 and FGF-2, as well as protein levels for "
        "NGL and FGL within ischemic vessel tissue. Ensure the logic is encapsulated in a "
        "reusable function and include comments explaining the biological context."
    )
    
    response = llm.prompt(prompt)

    # 2. Extract code to ensure the model actually provided a implementation
    code = tools.python.extract_code(response)
    assertions.assert_not_empty(
        code, 
        expectation="The model should provide a Python code block implementing the requested logic."
    )

    # 3. Use Judge LLM to evaluate the qualitative requirements
    assessment = assertions.assess_response_with_judge(
        criteria=[
            "The code or explanation specifically mentions FGF-1 and FGF-2.",
            "The code or explanation specifically mentions NGL and FGL protein levels.",
            "The logic pertains to ischemic vessel tissue and blood flow.",
            "The implementation handles or processes input strings as requested."
        ],
        response_text=response,
        judge_llm=kbench.judge_llm
    )

    # 4. Handle assessment results
    if assessment is None:
        assertions.assert_fail(expectation="Judge LLM failed to return a valid assessment.")
        return

    for result in assessment.results:
        assertions.assert_true(
            result.passed,
            expectation=f"Criterion '{result.criterion}' failed: {result.reason}"
        )

    # 5. Safe execution check of the generated code (optional validation)
    if code:
        exec_result = tools.python.script_runner.run_code(code)
        assertions.assert_equal(
            0, 
            exec_result.exit_code, 
            expectation=f"The generated code should be syntactically valid. Stderr: {exec_result.stderr}"
        )

if __name__ == "__main__":
    encrypt_biomarker_task.run(kbench.llm)