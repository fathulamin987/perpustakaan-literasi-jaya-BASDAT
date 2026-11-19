-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 14, 2026 at 06:25 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `perpustakaanliterasijaya`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `SP_KembalikanBuku` (IN `p_ID_Peminjaman` VARCHAR(10))   BEGIN
    DECLARE v_Cek_Pinjam INT DEFAULT 0;
    DECLARE v_ID_Buku VARCHAR(10);
    DECLARE v_Jatuh_Tempo DATE;
    DECLARE v_Status VARCHAR(20);
    DECLARE v_Status_Akhir VARCHAR(20);

    SELECT COUNT(*), MAX(ID_Buku), MAX(Tanggal_Jatuh_Tempo), MAX(Status_Peminjaman)
    INTO v_Cek_Pinjam, v_ID_Buku, v_Jatuh_Tempo, v_Status
    FROM Peminjaman WHERE ID_Peminjaman = p_ID_Peminjaman;

    IF v_Cek_Pinjam = 0 THEN
        SELECT 'GAGAL: ID_Peminjaman tidak ditemukan.' AS Pesan;
    ELSEIF v_Status <> 'Dipinjam' THEN
        SELECT CONCAT('GAGAL: Peminjaman tidak dapat diproses karena berstatus ', v_Status) AS Pesan;
    ELSE
        IF CURDATE() > v_Jatuh_Tempo THEN
            SET v_Status_Akhir = 'Terlambat';
        ELSE
            SET v_Status_Akhir = 'Dikembalikan';
        END IF;

        UPDATE Peminjaman
        SET Tanggal_Pengembalian = CURDATE(),
            Status_Peminjaman = v_Status_Akhir
        WHERE ID_Peminjaman = p_ID_Peminjaman;

        UPDATE Buku SET Jumlah_Stok = Jumlah_Stok + 1 WHERE ID_Buku = v_ID_Buku;

        SELECT CONCAT('BERHASIL: Buku dikembalikan dengan status ', v_Status_Akhir) AS Pesan;
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `SP_LaporanBukuBelumKembali` ()   BEGIN
    SELECT 
        b.Judul AS Judul_Buku,
        a.Nama_Anggota,
        p.Tanggal_Peminjaman,
        p.Tanggal_Jatuh_Tempo
    FROM Peminjaman p
    JOIN Buku b ON p.ID_Buku = b.ID_Buku
    JOIN Anggota a ON p.ID_Anggota = a.ID_Anggota
    WHERE p.Status_Peminjaman = 'Dipinjam'
    ORDER BY p.Tanggal_Jatuh_Tempo ASC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `SP_PinjamBuku` (IN `p_ID_Buku` VARCHAR(10), IN `p_ID_Anggota` VARCHAR(10))   BEGIN
    DECLARE v_Cek_Buku INT DEFAULT 0;
    DECLARE v_Cek_Anggota INT DEFAULT 0;
    DECLARE v_Stok INT DEFAULT 0;
    DECLARE v_ID_Baru VARCHAR(10);

    SELECT COUNT(*), IFNULL(MAX(Jumlah_Stok), 0)
    INTO v_Cek_Buku, v_Stok
    FROM Buku WHERE ID_Buku = p_ID_Buku;

    SELECT COUNT(*)
    INTO v_Cek_Anggota
    FROM Anggota WHERE ID_Anggota = p_ID_Anggota;

    IF v_Cek_Buku = 0 THEN
        SELECT 'GAGAL: ID_Buku tidak valid atau tidak ditemukan.' AS Pesan;
    ELSEIF v_Cek_Anggota = 0 THEN
        SELECT 'GAGAL: ID_Anggota tidak valid atau tidak terdaftar.' AS Pesan;
    ELSEIF v_Stok <= 0 THEN
        SELECT 'GAGAL: Stok buku habis (tidak tersedia untuk dipinjam).' AS Pesan;
    ELSE
        SELECT CONCAT('PJM', LPAD(IFNULL(MAX(CAST(SUBSTRING(ID_Peminjaman, 4) AS UNSIGNED)), 0) + 1, 3, '0'))
        INTO v_ID_Baru
        FROM Peminjaman;

        UPDATE Buku SET Jumlah_Stok = Jumlah_Stok - 1 WHERE ID_Buku = p_ID_Buku;

        INSERT INTO Peminjaman (
            ID_Peminjaman, ID_Buku, ID_Anggota,
            Tanggal_Peminjaman, Tanggal_Jatuh_Tempo,
            Tanggal_Pengembalian, Status_Peminjaman
        ) VALUES (
            v_ID_Baru, p_ID_Buku, p_ID_Anggota,
            CURDATE(), DATE_ADD(CURDATE(), INTERVAL 7 DAY),
            NULL, 'Dipinjam'
        );

        SELECT CONCAT('BERHASIL: Peminjaman dicatat dengan ID ', v_ID_Baru) AS Pesan;
    END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `anggota`
--

CREATE TABLE `anggota` (
  `ID_Anggota` varchar(10) NOT NULL,
  `Nama_Anggota` varchar(100) NOT NULL,
  `Alamat` varchar(255) NOT NULL,
  `No_Telepon` varchar(20) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Tanggal_Daftar` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `anggota`
--

INSERT INTO `anggota` (`ID_Anggota`, `Nama_Anggota`, `Alamat`, `No_Telepon`, `Email`, `Tanggal_Daftar`) VALUES
('AGT001', 'Ahmad Fauzi', 'Jl. Trunojoyo No. 10, Bangkalan', '081234567801', 'ahmad.fauzi@email.com', '2022-03-15'),
('AGT002', 'Siti Nurhaliza', 'Jl. Panglima Sudirman No. 25, Bangkalan', '081234567802', 'siti.nur@email.com', '2023-08-20'),
('AGT003', 'Budi Santoso', 'Jl. Soekarno Hatta No. 12, Bangkalan', '081234567803', 'budi.santoso@email.com', '2023-11-05'),
('AGT004', 'Dewi Lestari', 'Jl. Pemuda Kaffa No. 8, Bangkalan', '081234567804', 'dewi.lestari@email.com', '2024-02-10'),
('AGT005', 'Rizky Pratama', 'Jl. Raya Telang No. 45, Kamal', '081234567805', 'rizky.pratama@email.com', '2025-01-18');

-- --------------------------------------------------------

--
-- Table structure for table `buku`
--

CREATE TABLE `buku` (
  `ID_Buku` varchar(10) NOT NULL,
  `Judul` varchar(255) NOT NULL,
  `Penulis` varchar(100) NOT NULL,
  `Penerbit` varchar(100) NOT NULL,
  `Tahun_Terbit` int(11) NOT NULL,
  `ISBN` varchar(20) NOT NULL,
  `Jumlah_Stok` int(11) NOT NULL DEFAULT 0,
  `Kategori` varchar(50) NOT NULL
) ;

--
-- Dumping data for table `buku`
--

INSERT INTO `buku` (`ID_Buku`, `Judul`, `Penulis`, `Penerbit`, `Tahun_Terbit`, `ISBN`, `Jumlah_Stok`, `Kategori`) VALUES
('BK001', 'Basis Data Relasional Modern', 'Abdul Kadir', 'Andi Publisher', 2022, '978-602-01-1111-1', 3, 'Teknologi Informasi'),
('BK002', 'Algoritma dan Pemrograman Python', 'Rinaldi Munir', 'Informatika', 2023, '978-602-01-2222-2', 4, 'Teknologi Informasi'),
('BK003', 'Laskar Pelangi', 'Andrea Hirata', 'Bentang Pustaka', 2005, '978-979-30-6279-2', 3, 'Sastra'),
('BK004', 'Filosofi Teras', 'Henry Manampiring', 'Kompas', 2018, '978-602-41-2518-9', 7, 'Pengembangan Diri'),
('BK005', 'Sistem Informasi Manajemen', 'Jogiyanto HM', 'BPFE', 2021, '978-979-50-3333-3', 2, 'Sistem Informasi'),
('BK006', 'Jaringan Komputer Lanjut', 'Onno W. Purbo', 'Elex Media', 2024, '978-623-00-4444-4', 4, 'Teknologi Informasi');

-- --------------------------------------------------------

--
-- Table structure for table `peminjaman`
--

CREATE TABLE `peminjaman` (
  `ID_Peminjaman` varchar(10) NOT NULL,
  `ID_Buku` varchar(10) NOT NULL,
  `ID_Anggota` varchar(10) NOT NULL,
  `Tanggal_Peminjaman` date NOT NULL,
  `Tanggal_Jatuh_Tempo` date NOT NULL,
  `Tanggal_Pengembalian` date DEFAULT NULL,
  `Status_Peminjaman` enum('Dipinjam','Dikembalikan','Terlambat') NOT NULL DEFAULT 'Dipinjam'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `peminjaman`
--

INSERT INTO `peminjaman` (`ID_Peminjaman`, `ID_Buku`, `ID_Anggota`, `Tanggal_Peminjaman`, `Tanggal_Jatuh_Tempo`, `Tanggal_Pengembalian`, `Status_Peminjaman`) VALUES
('PJM001', 'BK001', 'AGT001', '2026-09-01', '2026-09-08', '2026-09-07', 'Dikembalikan'),
('PJM002', 'BK001', 'AGT002', '2026-09-10', '2026-09-17', '2026-09-16', 'Dikembalikan'),
('PJM003', 'BK002', 'AGT001', '2026-10-01', '2026-10-08', '2026-10-08', 'Dikembalikan'),
('PJM004', 'BK002', 'AGT003', '2026-10-05', '2026-10-12', '2026-10-15', 'Terlambat'),
('PJM005', 'BK003', 'AGT003', '2026-10-10', '2026-10-17', NULL, 'Terlambat'),
('PJM006', 'BK004', 'AGT004', '2026-11-12', '2026-11-19', '2026-11-14', 'Dikembalikan'),
('PJM007', 'BK005', 'AGT002', '2026-11-13', '2026-11-12', NULL, 'Terlambat'),
('PJM008', 'BK001', 'AGT005', '2026-11-14', '2026-11-21', NULL, 'Dipinjam'),
('PJM009', 'BK001', 'AGT005', '2026-11-14', '2026-11-21', NULL, 'Dipinjam');

--
-- Triggers `peminjaman`
--
DELIMITER $$
CREATE TRIGGER `TR_InsertStatusPeminjaman` BEFORE INSERT ON `peminjaman` FOR EACH ROW BEGIN
    IF NEW.Tanggal_Jatuh_Tempo < CURDATE() AND NEW.Tanggal_Pengembalian IS NULL THEN
        SET NEW.Status_Peminjaman = 'Terlambat';
    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `TR_UpdateStatusPeminjaman` BEFORE UPDATE ON `peminjaman` FOR EACH ROW BEGIN
    IF NEW.Tanggal_Jatuh_Tempo < CURDATE() AND NEW.Tanggal_Pengembalian IS NULL THEN
        SET NEW.Status_Peminjaman = 'Terlambat';
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_anggotaaktif`
-- (See below for the actual view)
--
CREATE TABLE `v_anggotaaktif` (
`ID_Anggota` varchar(10)
,`Nama_Anggota` varchar(100)
,`Jumlah_Peminjaman` bigint(21)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_bukupopuler`
-- (See below for the actual view)
--
CREATE TABLE `v_bukupopuler` (
`Judul` varchar(255)
,`Penulis` varchar(100)
,`Jumlah_Peminjaman` bigint(21)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_peminjamanterlambat`
-- (See below for the actual view)
--
CREATE TABLE `v_peminjamanterlambat` (
`Judul_Buku` varchar(255)
,`Nama_Anggota` varchar(100)
,`Tanggal_Peminjaman` date
,`Tanggal_Jatuh_Tempo` date
,`Tanggal_Pengembalian` date
);

-- --------------------------------------------------------

--
-- Structure for view `v_anggotaaktif`
--
DROP TABLE IF EXISTS `v_anggotaaktif`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_anggotaaktif`  AS SELECT `a`.`ID_Anggota` AS `ID_Anggota`, `a`.`Nama_Anggota` AS `Nama_Anggota`, count(`p`.`ID_Peminjaman`) AS `Jumlah_Peminjaman` FROM (`anggota` `a` join `peminjaman` `p` on(`a`.`ID_Anggota` = `p`.`ID_Anggota`)) GROUP BY `a`.`ID_Anggota`, `a`.`Nama_Anggota` HAVING count(`p`.`ID_Peminjaman`) >= 1 AND sum(case when `p`.`Status_Peminjaman` = 'Terlambat' then 1 else 0 end) = 0 ;

-- --------------------------------------------------------

--
-- Structure for view `v_bukupopuler`
--
DROP TABLE IF EXISTS `v_bukupopuler`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_bukupopuler`  AS SELECT `b`.`Judul` AS `Judul`, `b`.`Penulis` AS `Penulis`, count(`p`.`ID_Peminjaman`) AS `Jumlah_Peminjaman` FROM (`buku` `b` join `peminjaman` `p` on(`b`.`ID_Buku` = `p`.`ID_Buku`)) GROUP BY `b`.`ID_Buku`, `b`.`Judul`, `b`.`Penulis` HAVING count(`p`.`ID_Peminjaman`) >= 2 ;

-- --------------------------------------------------------

--
-- Structure for view `v_peminjamanterlambat`
--
DROP TABLE IF EXISTS `v_peminjamanterlambat`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_peminjamanterlambat`  AS SELECT `b`.`Judul` AS `Judul_Buku`, `a`.`Nama_Anggota` AS `Nama_Anggota`, `p`.`Tanggal_Peminjaman` AS `Tanggal_Peminjaman`, `p`.`Tanggal_Jatuh_Tempo` AS `Tanggal_Jatuh_Tempo`, `p`.`Tanggal_Pengembalian` AS `Tanggal_Pengembalian` FROM ((`peminjaman` `p` join `buku` `b` on(`p`.`ID_Buku` = `b`.`ID_Buku`)) join `anggota` `a` on(`p`.`ID_Anggota` = `a`.`ID_Anggota`)) WHERE `p`.`Status_Peminjaman` = 'Terlambat' ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `anggota`
--
ALTER TABLE `anggota`
  ADD PRIMARY KEY (`ID_Anggota`),
  ADD UNIQUE KEY `uq_anggota_email` (`Email`),
  ADD KEY `idx_anggota_tanggal_daftar` (`Tanggal_Daftar`);

--
-- Indexes for table `buku`
--
ALTER TABLE `buku`
  ADD PRIMARY KEY (`ID_Buku`),
  ADD UNIQUE KEY `uq_buku_isbn` (`ISBN`),
  ADD KEY `idx_buku_tahun_terbit` (`Tahun_Terbit`),
  ADD KEY `idx_buku_kategori` (`Kategori`);

--
-- Indexes for table `peminjaman`
--
ALTER TABLE `peminjaman`
  ADD PRIMARY KEY (`ID_Peminjaman`),
  ADD KEY `fk_peminjaman_buku` (`ID_Buku`),
  ADD KEY `fk_peminjaman_anggota` (`ID_Anggota`),
  ADD KEY `idx_peminjaman_status` (`Status_Peminjaman`),
  ADD KEY `idx_peminjaman_jatuh_tempo` (`Tanggal_Jatuh_Tempo`);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `peminjaman`
--
ALTER TABLE `peminjaman`
  ADD CONSTRAINT `fk_peminjaman_anggota` FOREIGN KEY (`ID_Anggota`) REFERENCES `anggota` (`ID_Anggota`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_peminjaman_buku` FOREIGN KEY (`ID_Buku`) REFERENCES `buku` (`ID_Buku`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
