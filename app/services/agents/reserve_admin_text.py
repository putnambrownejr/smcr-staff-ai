"""Shared reserve-administration knowledge blocks.

Several agents (Chief of Staff, Drill Prep, S-1, Surgeon, Chaplain, G-8) used to
carry their own copy of the Marine reserve admin-system chain and the Navy
reserve (NOSC/NROWS) admin chain.  Keeping one copy here means a superseded
MARADMIN or a renamed system is corrected once.

Every block states its own "as of" date; keep that current when editing.
"""

RESERVE_ADMIN_SYSTEMS = (
    "Reserve admin system chain (as of Sep 2026; verify against current MCO 1001R.1L and MARADMINs):\n"
    "- Drill Manager: captures IDT attendance → drives pay. Errors delay the entire pay cycle.\n"
    "- MROWS: generates ADT/AT orders. Submit with enough lead time for the approval chain.\n"
    "- DTS: travel authorizations and vouchers. Post-drill voucher completion is the most common drop.\n"
    "- MOL: self-service for LES, OMPF, training records. Marines should verify before drill.\n"
    "- MCTFS/Unit Diary: authoritative system of record for all status changes.\n"
    "- MRRS/RHRP/PHA: medical readiness tracking — dental, PHA, IMR must be current.\n"
)

RESERVE_POLICY_BASELINES = (
    "Key policy baselines (as of Sep 2026; verify before briefing):\n"
    "- 48 IDT periods + 14 days AT per year (MCO 1001R.1L w/CH-2).\n"
    "- MARADMIN 157/25: IDT travel reimbursement up to $750 per qualifying trip for designated billets "
    "outside normal commuting distance.\n"
    "- Common unit planning triggers (rule of thumb, not policy): T-45 MROWS submission, "
    "T-30 DTS authorization, T-15 final coordination (billeting, ranges, chow).\n"
)

RESERVE_FRICTION_POINTS = (
    "Reserve friction points to front-load:\n"
    "- Asynchronous admin between drills (things break during the 28-day gap).\n"
    "- Dual-status civilians with employer notification requirements.\n"
    "- Geographic dispersion — Marines traveling from multiple states.\n"
    "- System fragmentation across 6+ platforms with different access requirements.\n"
    "- Compressed training year — 48 IDT periods to accomplish a full training plan.\n"
)

NAVY_RESERVE_ADMIN = (
    "Navy personnel attached to Marine units (corpsmen, chaplains, RPs) — different admin chain "
    "(as of Sep 2026; verify with the supporting NOSC):\n"
    "- They are Navy reservists. Orders, pay, and admin run through their NOSC (Navy Operational "
    "Support Center, the Navy equivalent of I&I), not the Marine unit.\n"
    "- The Marine unit is the gaining command (operational/training); the NOSC is the supporting "
    "command (admin/orders/pay).\n"
    "- Orders go through NROWS (Navy Reserve Order Writing System), NOT MROWS. The Marine unit "
    "OpsO/S-1 writes a letter of request (dates, location, funding source, justification); the NOSC "
    "submits in NROWS; CNRFC approves — not MARFORRES.\n"
    "- Start NROWS requests at T-60 minimum (vs T-45 for MROWS). Last-minute AT additions for Navy "
    "personnel are very hard.\n"
    "- Pay issues route through the NOSC (MyPay/NSIPS), not the Marine S-1.\n"
    "- Medical/dental readiness is tracked in MRRS; corrections route through the NOSC.\n"
    "- NSIPS is the Navy equivalent of MOL for service records.\n"
    "- Keep a tracker of every Navy member: name, rate, NOSC assignment, NROWS status, and upcoming "
    "order requirement dates.\n"
)
