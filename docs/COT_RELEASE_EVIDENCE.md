[EN](COT_RELEASE_EVIDENCE.md) | [RU](COT_RELEASE_EVIDENCE.ru.md)

# COT publication evidence

The release manifest contains **four confirmed historical report dates**, not a complete history. It is not enough for the planned train, validation and test experiment, nor representative of normal publication: these observations all fall in the 2023 ION disruption. No strategy or model result is established by this manifest.

## Evidence and conservative timestamps

The CFTC's [historical special announcements](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm) document both a statement that the report is being issued **today** and its report date:

| Report date | Announcement says issued | Manifest `available_at` |
| --- | --- | --- |
| 2023-01-31 | 2023-02-24 | 2023-02-25 05:00 UTC |
| 2023-02-07 | 2023-03-03 | 2023-03-04 05:00 UTC |
| 2023-02-14 | 2023-03-08 | 2023-03-09 05:00 UTC |
| 2023-02-21 | 2023-03-10 | 2023-03-11 05:00 UTC |

The time in the manifest is a **conservative eligibility cutoff**, not an assertion of the actual release instant. These announcements do not specify the time. Using 05:00 UTC on the following day waits until at least midnight in US Eastern time, including daylight saving time. The manifest's existing column name `available_at` is therefore interpreted as "known available no later than this conservative time." The evidence is a CFTC same-day statement, not direct observation of a historical server log. Later revisions of archived positions are not ruled out.

## Missing coverage and limitations

- The [CFTC historical archive](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm) explicitly labels its displayed dates as report dates, not release dates. It does not by itself substantiate publication timing.
- The CFTC [release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm) says the schedule is tentative and holidays may delay release. Do not treat a planned publication as an actual historical release.
- The December 2025 special-announcement table describes *intended* catch-up dates, and a previous schedule was revised. Without separate retrospective evidence of publication, those entries are omitted.
- Other 2023 announcements refer to previously scheduled publication dates without explicitly naming the report's observation date. Those are omitted until an independent linkage is documented.
- CFTC's October 2026 [announcement](https://www.cftc.gov/PressRoom/PressReleases/9316-26) describes a future twice-weekly release plan. Do not assume the former weekly timetable after a transition without verified evidence.
- The public position archive may contain subsequent corrections. A confirmed release date does not verify that today's downloaded position values reproduce the values originally published. The project must disclose this vintage limitation.

## Source and timing contract reviewed 2026-11-21

- **COT observation and release are separate facts.** The report's Tuesday `report_date` is the position observation date. The CFTC release schedule says reports are ordinarily published at 3:30 p.m. Eastern and usually cover the previous Tuesday, but it is tentative and federal holidays can delay publication by one or two days. The historical archive exposes report dates and annual report files; it does not provide a complete per-report release log. A schedule entry or weekday pattern is not evidence that a particular report was actually public at that time.
- **Selected COT scope.** The CFTC's [Historical Compressed archive](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm) lists annual Disaggregated Futures Only reports from September 2009, in text and Excel formats. The project intends to use COMEX gold and silver market rows and fields for open interest and trader positions. Validate report type, market identity, CFTC market code, report date, numeric fields, duplicates and missing rows against the downloaded file before ingestion. Archive availability is not release-time or vintage evidence. No license conclusion beyond the public availability of the reports was verified in this review; preserve source attribution and recheck applicable provider notices before redistribution.
- **COT eligibility.** Only a report-date/publication-date pair backed by a contemporaneous CFTC notice that identifies the report may enter `config/release_dates.csv`. When the notice says “today” but omits the hour, the existing next-day 05:00 UTC convention is a conservative cutoff; it is not the observed release instant. Join a report only when `available_at <= signal_at`. Exclude unmatched, ambiguous, late, or unconfirmed reports and report the resulting coverage gap. CFTC announced in October 2026 a plan to move to twice-weekly publications by the end of 2026; verify the actual transition and revised release evidence before applying the old weekly rule beyond it.
- **ETF and other market bars.** NYSE publishes a core session of 9:30 a.m.–4:00 p.m. Eastern and early-close/holiday calendars. The feature signal is timestamped at the actual GLD/SLV session close using the exchange calendar; a daily bar for that session is eligible only after that close. Snapshot request-start metadata prevents a bar still forming when requested from later being treated as complete during offline replay. Yahoo/yfinance history is a retrieved vendor series, not a point-in-time archive: provider adjustments and revisions may reflect later information. The yfinance documentation says it is unaffiliated with Yahoo, points users to Yahoo's terms, and describes the service as intended for personal use; this project has not independently established commercial redistribution rights, a formal service-level agreement, or numeric rate limits. Keep raw files local and recheck current terms before wider use.
- **Optional series and failure behavior.** BTC and NVDA are required under current configuration; SOL, ETH, ZEC, S&P 500, Nasdaq and Dow inputs are optional. Each optional input must retain its own source, retrieval, timestamp and failure metadata. Missing optional series must not silently change the required target universe; mark their feature values missing or explicitly disable them through configuration. FRED remains out of scope until historical vintages and release availability are established. No provider response, agreement on data rights, download, or numeric rate limit was verified by this review.

Next steps: seek a durable per-report historical release log or archived contemporaneous CFTC publication notices, including holiday and shutdown periods; document each observation-to-publication pairing, prefer after-the-day UTC cutoffs when exact instants are unavailable, and retain evidence before expanding the manifest. The third-party [ZipLime methodology](https://huggingface.co/datasets/ZipLime/commitments-of-traders/blob/main/PIPELINE.md) is a lead, not ground truth: it uses estimated rules and planned dates for part of its history. Validate its source-by-source evidence independently before use.

Checked 2026-11-21 using official CFTC, NYSE and yfinance documentation through the web research tool. A direct shell request to `www.cftc.gov` failed DNS resolution in this environment. Yahoo's terms page could not be opened directly in the research tool; its limitations above are confined to what the yfinance documentation states. No source data was downloaded by this investigation.
