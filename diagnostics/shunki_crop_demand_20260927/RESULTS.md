# Crop-chain feasibility decision — 2026-09-27 01:46 UTC

The three unchanged-main traces reproduce the previous losses, all DONE.
Filtering the apparent spare work windows by the actual late crop coordinates
and melon maturity leaves only four of eight early plots with a same-day,
three-command window at ages 10–12 in each BAKERY/PET case, and zero of the
two early plots in the PET/PET case. Many other windows precede maturity or
occur after melons start decaying. The existing schedule replaces these plots
with carrots/wheat around days 22–25, which also constrains a second melon crop.

The installed 1.32.7 engine confirms that melon harvest removes the plant,
water increases yield only at ages 6–12, and a new plant needs watering on
its planting day. Its initial unwatered counter is one. Three same-tile
commands do not alone prove that a replacement crop will subsequently receive
water and reach a scheduled harvest before the original field conversion.

Decision: reject a local strawberry-to-melon substitution as the next
candidate. It would require broader worker rescheduling and has no demonstrated
competitive gain. No candidate was built, and no win-rate test was performed.
The passive traces and `audit.json` remain available for a future scheduler.
