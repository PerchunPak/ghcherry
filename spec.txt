// This is a copy of excellent https://stackoverflow.com/a/58672227/22235705
// for reference
//
// This outlines the algorithm in basic pseudocode, and this script was built
// on top of this

// here is a commit, for example, from a pull request:
listOfCommits = GET /repos/$owner/$repo/pulls/$number/commits
commit = listOfCommits.head // the first one in the list

// Here is the branch we want to cherry-pick to:
branch = GET /repos/$owner/$repo/branches/$branchName
branchSha = branch.commit.sha
branchTree = branch.commit.commit.tree.sha

// Create a temporary commit on the branch, which extends as a sibling of
// the commit we want but contains the current tree of the target branch:
parentSha = commit.parents.head // first parent -- there should only be one
tempCommit = POST /repos/$owner/$repo/git/commits { "message": "temp",
                                                    "tree": branchTree,
                                                    "parents": [parentSha] }

// Now temporarily force the branch over to that commit
PATCH /repos/$owner/$repo/git/refs/heads/$refName { sha = tempCommit.sha,
                                                    force = true }

// Merge the commit we want into this mess:
merge = POST /repos/$owner/$repo/merges { "base": branchName
                                  "head": commit.sha }

// and get that tree!
mergeTree = merge.commit.tree.sha

// Now that we know what the tree should be, create the cherry-pick commit.
// Note that branchSha is the original from up at the top.
cherry = POST /repos/$owner/$repo/git/commits { "message": "looks good!",
                                                "tree": mergeTree,
                                                "parents": [branchSha] }

// Replace the temp commit with the real commit:
PATCH /repos/$owner/$repo/git/refs/heads/$refName { sha = cherry.sha,
                                                    force = true }

// Done!
