# Get the commit message from the command line argument
param(
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage
)

# Add all changes
git add .

# Commit with the provided message
git commit -m $CommitMessage

# Push to the current branch
git push

Write-Host "Changes have been committed and pushed!" -ForegroundColor Green 