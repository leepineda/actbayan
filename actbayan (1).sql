-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 08, 2026 at 11:15 AM
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
-- Database: `actbayan`
--

-- --------------------------------------------------------

--
-- Table structure for table `accounts`
--

CREATE TABLE `accounts` (
  `account_id` int(11) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `middle_name` varchar(50) NOT NULL,
  `dob` date NOT NULL,
  `profile_photo` blob NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `accounts`
--

INSERT INTO `accounts` (`account_id`, `first_name`, `last_name`, `middle_name`, `dob`, `profile_photo`) VALUES
(1, 'Fred', 'Rick', 'Saging', '2026-04-12', ''),
(2, 'Juswa', 'VHAAS', 'fsf', '2026-05-26', '');

-- --------------------------------------------------------

--
-- Table structure for table `contacts`
--

CREATE TABLE `contacts` (
  `contact_id` int(11) NOT NULL,
  `account_id` int(11) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone_number` varchar(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `contacts`
--

INSERT INTO `contacts` (`contact_id`, `account_id`, `email`, `phone_number`) VALUES
(1, 1, 'sanfrbs26@gmail.com', NULL),
(2, 2, NULL, '09280503740');

--
-- Triggers `contacts`
--
DELIMITER $$
CREATE TRIGGER `passcontact` AFTER INSERT ON `contacts` FOR EACH ROW BEGIN
    IF NEW.email IS NOT NULL THEN
        INSERT INTO usercreds(contact_id, emorph)
        VALUES (NEW.contact_id, NEW.email);
    END IF;

    IF NEW.phone_number IS NOT NULL THEN
        INSERT INTO usercreds(contact_id, emorph)
        VALUES (NEW.contact_id, NEW.phone_number);
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `credentials`
--

CREATE TABLE `credentials` (
  `cred_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `pass_id` int(11) DEFAULT NULL,
  `failed_attempts` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `credentials`
--

INSERT INTO `credentials` (`cred_id`, `user_id`, `pass_id`, `failed_attempts`) VALUES
(1, 1, 1, NULL),
(2, 2, 2, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `password`
--

CREATE TABLE `password` (
  `pass_id` int(11) NOT NULL,
  `password` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `password`
--

INSERT INTO `password` (`pass_id`, `password`) VALUES
(1, 'lolo'),
(2, 'haha');

--
-- Triggers `password`
--
DELIMITER $$
CREATE TRIGGER `passpass` AFTER INSERT ON `password` FOR EACH ROW BEGIN
	UPDATE credentials
	SET pass_id = NEW.pass_id
	WHERE cred_id = (SELECT MAX(cred_id) FROM credentials); 
end
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `registration`
--

CREATE TABLE `registration` (
  `registration_id` int(11) NOT NULL,
  `email_address` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `phone_number` varchar(11) NOT NULL,
  `created_at` date NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `report_id` int(11) NOT NULL,
  `account_id` int(11) NOT NULL,
  `category` varchar(50) NOT NULL,
  `title` varchar(100) NOT NULL,
  `location` varchar(255) NOT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `description` text NOT NULL,
  `status` varchar(50) DEFAULT 'Pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reports`
--

INSERT INTO `reports` (`report_id`, `account_id`, `category`, `title`, `location`, `image_url`, `description`, `status`, `created_at`) VALUES
(1, 1, 'Safety', 'sfdfds', 'dfdsfds', 'static/uploads/concerns/concern_1_1778228815_Screenshot (27).png', 'fsfsdfsd', 'Pending', '2026-05-08 08:26:55');

-- --------------------------------------------------------

--
-- Table structure for table `report_update`
--

CREATE TABLE `report_update` (
  `reportupd_id` int(11) NOT NULL,
  `account_id` int(11) DEFAULT NULL,
  `report_id` int(11) DEFAULT NULL,
  `image_url` text DEFAULT NULL,
  `description` text DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `report_update`
--

INSERT INTO `report_update` (`reportupd_id`, `account_id`, `report_id`, `image_url`, `description`, `submitted_at`) VALUES
(1, 2, 1, 'static/uploads/update_1_1778229551_Screenshot (68).png', 'Ang sarap ko', '2026-05-08 16:39:11');

-- --------------------------------------------------------

--
-- Table structure for table `role`
--

CREATE TABLE `role` (
  `role_id` int(11) NOT NULL,
  `role` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `role`
--

INSERT INTO `role` (`role_id`, `role`) VALUES
(1, 'Resident'),
(2, 'LGU Official');

-- --------------------------------------------------------

--
-- Table structure for table `usercreds`
--

CREATE TABLE `usercreds` (
  `user_id` int(11) NOT NULL,
  `contact_id` int(11) DEFAULT NULL,
  `emorph` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `usercreds`
--

INSERT INTO `usercreds` (`user_id`, `contact_id`, `emorph`) VALUES
(1, 1, 'sanfrbs26@gmail.com'),
(2, 2, '09280503740');

--
-- Triggers `usercreds`
--
DELIMITER $$
CREATE TRIGGER `insertuser` AFTER INSERT ON `usercreds` FOR EACH ROW BEGIN
	INSERT INTO credentials (user_id) VALUES (NEW.user_id);
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `user_role`
--

CREATE TABLE `user_role` (
  `user_id` int(11) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_role`
--

INSERT INTO `user_role` (`user_id`, `role_id`) VALUES
(1, 1),
(2, 2);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `accounts`
--
ALTER TABLE `accounts`
  ADD PRIMARY KEY (`account_id`);

--
-- Indexes for table `contacts`
--
ALTER TABLE `contacts`
  ADD PRIMARY KEY (`contact_id`),
  ADD KEY `account_id` (`account_id`);

--
-- Indexes for table `credentials`
--
ALTER TABLE `credentials`
  ADD PRIMARY KEY (`cred_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `pass_id` (`pass_id`);

--
-- Indexes for table `password`
--
ALTER TABLE `password`
  ADD PRIMARY KEY (`pass_id`);

--
-- Indexes for table `registration`
--
ALTER TABLE `registration`
  ADD PRIMARY KEY (`registration_id`),
  ADD UNIQUE KEY `email_address` (`email_address`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`report_id`);

--
-- Indexes for table `report_update`
--
ALTER TABLE `report_update`
  ADD PRIMARY KEY (`reportupd_id`),
  ADD KEY `account_id` (`account_id`),
  ADD KEY `report_id` (`report_id`);

--
-- Indexes for table `role`
--
ALTER TABLE `role`
  ADD PRIMARY KEY (`role_id`);

--
-- Indexes for table `usercreds`
--
ALTER TABLE `usercreds`
  ADD PRIMARY KEY (`user_id`),
  ADD KEY `contact_id` (`contact_id`);

--
-- Indexes for table `user_role`
--
ALTER TABLE `user_role`
  ADD KEY `user_id` (`user_id`),
  ADD KEY `role_id` (`role_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `contacts`
--
ALTER TABLE `contacts`
  MODIFY `contact_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `credentials`
--
ALTER TABLE `credentials`
  MODIFY `cred_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `password`
--
ALTER TABLE `password`
  MODIFY `pass_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `registration`
--
ALTER TABLE `registration`
  MODIFY `registration_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `report_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `report_update`
--
ALTER TABLE `report_update`
  MODIFY `reportupd_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `role`
--
ALTER TABLE `role`
  MODIFY `role_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `usercreds`
--
ALTER TABLE `usercreds`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `contacts`
--
ALTER TABLE `contacts`
  ADD CONSTRAINT `contacts_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`);

--
-- Constraints for table `credentials`
--
ALTER TABLE `credentials`
  ADD CONSTRAINT `credentials_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `usercreds` (`user_id`),
  ADD CONSTRAINT `credentials_ibfk_2` FOREIGN KEY (`pass_id`) REFERENCES `password` (`pass_id`);

--
-- Constraints for table `report_update`
--
ALTER TABLE `report_update`
  ADD CONSTRAINT `report_update_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`),
  ADD CONSTRAINT `report_update_ibfk_2` FOREIGN KEY (`report_id`) REFERENCES `reports` (`report_id`);

--
-- Constraints for table `usercreds`
--
ALTER TABLE `usercreds`
  ADD CONSTRAINT `usercreds_ibfk_1` FOREIGN KEY (`contact_id`) REFERENCES `contacts` (`contact_id`);

--
-- Constraints for table `user_role`
--
ALTER TABLE `user_role`
  ADD CONSTRAINT `user_role_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `usercreds` (`user_id`),
  ADD CONSTRAINT `user_role_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `role` (`role_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
