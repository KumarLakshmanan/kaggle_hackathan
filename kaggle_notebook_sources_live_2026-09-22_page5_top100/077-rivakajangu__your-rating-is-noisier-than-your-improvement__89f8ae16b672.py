# The problem, in two numbers.
identical_binary_spread = 268   # the same file, same hash, submitted twice
rebuilt_policy_spread   = 398   # the same policy rebuilt, submitted twice
my_gap_to_top_10        = 355   # points I need to reach a prize spot

print("spread between two runs of an IDENTICAL binary:", identical_binary_spread)
print("spread when the same policy is rebuilt:       ", rebuilt_policy_spread)
print("distance I am trying to close:                ", my_gap_to_top_10)
print()
print("The larger figure alone exceeds the gap I am trying to close.")
print("Even the smaller one is three quarters of it.")
print("The thing I am measuring is about the size of the error in my ruler.")

# Worth running on your own practice set before you trust it.
comfortable, narrow, losses = 209, 37, 12
total = comfortable + narrow + losses
close = narrow + losses

print("opponents in the set:", total)
print("games that are actually close: %d (%.0f%%)" % (close, 100*close/total))
print("one game is worth %.4f of the win rate" % (1/total))
print()
print("To beat the noise, a change has to flip several of those %d games," % close)
print("not several of %d. That is a much harder bar than it looks." % total)