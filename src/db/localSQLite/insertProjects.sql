-- Active: 1724378630371@@127.0.0.1@3306
-- Active: 1725846508072@@127.0.0.1@3306
-- Active: 1724378630371@@127.0.0.1@3306
select * from "Projects";

DELETE FROM "Projects";

insert into
    "Projects" (
        "ProjectID", "ProjectName", "ProjectDescription"
    ) VALUES (
        0, 'Installer', 'Installer'
    );

insert into
    "Projects" (
        "ProjectID", "ProjectName", "ProjectDescription"
    ) VALUES (
        1, 'Webex APP', 'Webex APP'
    );

insert into
    "Projects" (
        "ProjectID", "ProjectName", "ProjectDescription"
    ) VALUES (
        2, 'Webex Message', 'Webex Message'
    );

insert into
    "Projects" (
        "ProjectID", "ProjectName", "ProjectDescription"
    ) VALUES (
        3, 'Webex Meeting', 'Webex Meeting'
    );

insert into
    "Projects" (
        "ProjectID", "ProjectName", "ProjectDescription"
    ) VALUES (
        4, 'Webex Calling', 'Webex Calling'
    );