-- PTAC Pro Tracker: Row-Level Security policies
-- Run this in Supabase → SQL Editor if the app gets:
--   "new row violates row-level security policy for table ..."
--
-- Your schema already has a policy on ptac_units. The other tables
-- also need policies when RLS is enabled and the app uses the anon key.

-- ptac_units (safe to re-run)
ALTER TABLE ptac_units ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_all_ptac_management" ON ptac_units;
CREATE POLICY "allow_all_ptac_management" ON ptac_units
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- custody_transfers — required for custody transfer, Doyle returns, etc.
ALTER TABLE custody_transfers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_all_custody_transfers" ON custody_transfers;
CREATE POLICY "allow_all_custody_transfers" ON custody_transfers
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- pm_logs — required for PM checklist submissions
ALTER TABLE pm_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_all_pm_logs" ON pm_logs;
CREATE POLICY "allow_all_pm_logs" ON pm_logs
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- onsite_repairs — required for onsite repair logging
ALTER TABLE onsite_repairs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_all_onsite_repairs" ON onsite_repairs;
CREATE POLICY "allow_all_onsite_repairs" ON onsite_repairs
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- doyle_repairs — required for Doyle portal completions
ALTER TABLE doyle_repairs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_all_doyle_repairs" ON doyle_repairs;
CREATE POLICY "allow_all_doyle_repairs" ON doyle_repairs
  FOR ALL
  USING (true)
  WITH CHECK (true);
