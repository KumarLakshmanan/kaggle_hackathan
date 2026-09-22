import kaggle_benchmarks as kbench

@kbench.task(name="compose alternating rhyme lighthouse poem")
def compose_rhyme_poem(llm):
    prompt = (
        "Write a six-line poem about a lighthouse keeper who has never seen the ocean dry. "
        "The rhyme scheme must be alternating ABABAB. "
        "The very last word of the poem must rhyme with 'tide'."
    )
    
    response = llm.prompt(prompt)

    # Use a judge to evaluate the structural and thematic requirements
    assessment = kbench.assertions.assess_response_with_judge(
        criteria=[
            "The poem contains exactly six lines.",
            "The rhyme scheme is alternating ABABAB.",
            "The poem is about a lighthouse keeper who has never seen the ocean dry.",
            "The last word of the poem rhymes with 'tide'."
        ],
        response_text=response,
        judge_llm=kbench.judge_llm
    )

    if assessment is None:
        kbench.assertions.assert_fail(expectation="Judge LLM failed to return a valid assessment.")
        return

    # Process judge results as assertions
    for result in assessment.results:
        kbench.assertions.assert_true(
            result.passed,
            expectation=f"Criterion '{result.criterion}' failed: {result.reason}"
        )

compose_rhyme_poem.run(kbench.llm)