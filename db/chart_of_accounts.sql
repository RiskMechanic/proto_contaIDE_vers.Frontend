-- Piano dei Conti standard italiano (bootstrap)
-- Struttura: codice, nome, classe, parent_code

INSERT INTO accounts (code, name, class, parent_code) VALUES
-- Attività (A)
('1000', 'ATTIVO', 'A', NULL),
('1100', 'Immobilizzazioni immateriali', 'A', '1000'),
('1200', 'Immobilizzazioni materiali', 'A', '1000'),
('1300', 'Immobilizzazioni finanziarie', 'A', '1000'),
('1400', 'Attivo circolante', 'A', '1000'),
('1410', 'Crediti verso clienti', 'A', '1400'),
('1420', 'Rimanenze', 'A', '1400'),
('1430', 'Disponibilità liquide', 'A', '1400'),
('1431', 'Cassa', 'A', '1430'),
('1432', 'Banca c/c', 'A', '1430'),

-- Passività (P)
('2000', 'PASSIVO', 'P', NULL),
('2100', 'Patrimonio netto', 'P', '2000'),
('2200', 'Fondi rischi e oneri', 'P', '2000'),
('2300', 'Debiti', 'P', '2000'),
('2310', 'Debiti verso fornitori', 'P', '2300'),
('2320', 'Debiti tributari', 'P', '2300'),
('2330', 'Debiti finanziari', 'P', '2300'),

-- Costi (C)
('3000', 'COSTI', 'C', NULL),
('3100', 'Acquisti di materie prime e merci', 'C', '3000'),
('3200', 'Costi per servizi', 'C', '3000'),
('3300', 'Costi per il personale', 'C', '3000'),
('3400', 'Ammortamenti e svalutazioni', 'C', '3000'),
('3500', 'Oneri finanziari', 'C', '3000'),
('3600', 'Oneri tributari', 'C', '3000'),

-- Ricavi (R)
('4000', 'RICAVI', 'R', NULL),
('4100', 'Vendite e prestazioni', 'R', '4000'),
('4200', 'Altri ricavi e proventi', 'R', '4000'),
('4300', 'Proventi finanziari', 'R', '4000');
