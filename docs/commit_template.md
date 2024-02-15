# Commit Message Template

This document provides a commit message template for the BattleBot project. Follow these guidelines to create clear and informative commit messages that align with our coding standards.

## Commit Message Format

``` markdown
Project Name: [Your Project Name]
Commit Type: [Type of Commit]

[Short one-line description of the change]

[Optional longer description of the change, if needed]

[Additional context or notes, such as related issues or other details]

Signed-off-by: [Your Name] <[Your Email]>
```


- **Project Name**: Replace with the name of the project you're working on.

- **Commit Type**: Specify the type of commit. Common types include:
  - Feature: Adding new features or functionality.
  - Fix: Correcting bugs or issues.
  - Refactor: Making code improvements without changing functionality.
  - Docs: Updating documentation.
  - Test: Adding or modifying tests.
  - Chore: Routine tasks, maintenance, or code clean-up.

- **Short one-line description of the change**: Provide a brief and concise summary of the change made in this commit. Use the imperative mood (e.g., "Add," "Fix," "Update") and keep it under 72 characters.

- **Optional longer description of the change, if needed**: Include more details about the changes made, if necessary. Use bullet points or paragraphs to explain the why and how of the change.

- **Additional context or notes, such as related issues or other details**: Mention any related issues, links, or additional context that helps reviewers understand the change better.

- **Signed-off-by**: Sign your commit with your name and email address.

## Example Commit Message

```
Project Name: BattleBot
Commit Type: Feature
Add Django model for user profiles

- Created a new Django model for user profiles.
- Added fields for user bio, profile picture, and contact information.

Related Issue: #123

Signed-off-by: Butros Groot <butros@example.com>
```

## Commit Message Guidelines

- Use clear and descriptive commit messages.
- Keep lines within 72 characters to ensure readability.
- Follow the imperative mood in the one-line description (e.g., "Add," "Fix," "Update").
- Provide context and explanations in the optional longer description if the change is not self-explanatory.
- Reference related issues by including their issue numbers (e.g., "Related Issue: #123").
- Sign your commits to indicate authorship.

By following this commit message template and guidelines, we aim to maintain consistency and clarity in our commit history.

## Setup Commit Template in Git

To set up this commit template in Git, run the following command:

``` bash
git config commit.template <path/to/docs/commit_message_template.txt>
```


**Author:** Butros Groot

**Date:** 14-02-2024
