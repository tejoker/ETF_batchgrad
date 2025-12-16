import re
import os
from bs4 import BeautifulSoup as bs
import time
import logging
import json
from typing import List, Dict
import jsonschema



class LinkedinScraper:
    def __init__(self, profile: str, driver: object, save: bool) -> None:
        self.profile = bs(profile, "lxml")
        self.driver = driver
        self.save = save
        self.url = self.driver.current_url
        self.metadata = self.get_metadata()
        
        # Basic profile information
        self.name = self.get_name()
        self.headline = self.get_headline()
        self.location = self.get_location()
        self.about = self.get_about()
        self.profile_photo_url = self.get_profile_photo_url()
        self.background_photo_url = self.get_background_photo_url()
        self.profile_metadata = self.get_profile_metadata()
        
        # Existing sections
        self.experience = (
            self.get_experience()
            if self.metadata["sectionExists"]["experience"]
            else [self.get_dict("experience")]
        )
        self.education = (
            self.get_education()
            if self.metadata["sectionExists"]["education"]
            else [self.get_dict("education")]
        )
        
        # New sections
        self.certifications = (
            self.get_certifications()
            if self.metadata["sectionExists"].get("certifications", False)
            else [self.get_dict("certification")]
        )
        self.projects = self.get_projects()
        self.publications = self.get_publications()
        self.languages = self.get_languages()
        self.honors = self.get_honors()
        self.courses = self.get_courses()
        
        # Existing sections
        self.volunteering = (
            self.get_volunteering()
            if self.metadata["sectionExists"]["volunteering_experience"]
            else [self.get_dict("volunteering")]
        )
        self.skills = (
            self.get_skills()
            if self.metadata["sectionExists"]["skills"]
            else [self.get_dict("skills")]
        )
        
        self.output = self.get_json_output()


    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and fixing formatting"""
        if not text:
            return None
        # Remove excessive whitespace and newlines
        text = " ".join(text.split())
        # Add space after commas if missing
        text = re.sub(r',([^\s])', r', \1', text)
        # Add space between month and year (e.g., "May2023" → "May 2023")
        text = re.sub(r'([A-Za-z])(\d{4})', r'\1 \2', text)
        return text.strip()

    def get_name(self) -> str or None:
        try:
            # Try primary selector
            name_div = self.profile.find("div", attrs={"class": "pv-text-details__left-panel"})
            if name_div:
                h1 = name_div.find("h1")
                if h1:
                    return self.clean_text(h1.text)
            
            # Fallback 1: Try direct h1 search
            h1 = self.profile.find("h1", attrs={"class": lambda x: x and "text-heading-xlarge" in x})
            if h1:
                return self.clean_text(h1.text)
            
            # Fallback 2: Try any h1 in the top card area
            top_card = self.profile.find("div", attrs={"class": lambda x: x and "pv-top-card" in x})
            if top_card:
                h1 = top_card.find("h1")
                if h1:
                    return self.clean_text(h1.text)
            
            logging.error("Name not found with any selector")
            return None
        except Exception as e:
            logging.exception(e)
            logging.error("Error extracting name")
            return None

    def get_headline(self) -> str or None:
        """Extract professional headline"""
        try:
            # Try primary selector
            headline = self.profile.find(
                "div", 
                attrs={"class": "text-body-medium break-words"}
            )
            if headline:
                return self.clean_text(headline.text)
            
            # Fallback 1: Look for headline in pv-text-details
            text_details = self.profile.find("div", attrs={"class": "pv-text-details__left-panel"})
            if text_details:
                # Headline is usually the second div after name
                divs = text_details.find_all("div", recursive=False)
                if len(divs) >= 2:
                    return self.clean_text(divs[1].text)
            
            # Fallback 2: Look for any div with headline-like class
            headline = self.profile.find("div", attrs={"class": lambda x: x and "headline" in x.lower()})
            if headline:
                return self.clean_text(headline.text)
                
        except Exception as e:
            logging.exception(e)
            logging.error("Headline not found")
        return None

    def get_location(self) -> str or None:
        try:
            # Try primary selector
            location = self.profile.find(
                "span",
                attrs={"class": "text-body-small inline t-black--light break-words"},
            )
            if location:
                return self.clean_text(location.text)
            
            # Fallback 1: Look for location in pv-text-details area
            text_details = self.profile.find("div", attrs={"class": "pv-text-details__left-panel"})
            if text_details:
                location_span = text_details.find("span", attrs={"class": lambda x: x and "text-body-small" in x})
                if location_span:
                    return self.clean_text(location_span.text)
            
            # Fallback 2: Look for any span with location-like content
            all_spans = self.profile.find_all("span", attrs={"class": lambda x: x and "text-body-small" in x})
            for span in all_spans:
                text = span.text.strip()
                # Location usually doesn't have numbers or special chars
                if text and len(text) > 3 and len(text) < 100:
                    return self.clean_text(text)
                    
        except Exception as e:
            logging.exception(e)
            logging.error("Location not found")
        return None

    def get_about(self) -> str or None:
        """Extract about/summary section"""
        try:
            # Find the about section
            about_section = self.profile.find("section", attrs={"id": "about"})
            if not about_section:
                about_section = self.profile.find("div", attrs={"id": "about"})
            
            if about_section:
                # Look for visually-hidden span (accessibility text)
                about_text = about_section.find(
                    "span", 
                    attrs={"class": "visually-hidden"}
                )
                
                if about_text:
                    return self.clean_text(about_text.text)
                
                # Fallback: look for visible text
                about_div = about_section.find(
                    "div",
                    attrs={"class": "display-flex ph5 pv3"}
                )
                if about_div:
                    return self.clean_text(about_div.text)
                    
        except Exception as e:
            logging.exception(e)
            logging.error("About section not found")
        return None

    def get_profile_photo_url(self) -> str or None:
        """Extract profile picture URL"""
        try:
            # Try main profile picture
            img = self.profile.find(
                "img",
                attrs={"class": "pv-top-card-profile-picture__image"}
            )
            
            if not img:
                # Alternative selector
                img = self.profile.find(
                    "img",
                    attrs={"class": lambda x: x and "profile-photo" in x}
                )
            
            if img:
                src = img.get("src")
                # LinkedIn often uses data-delayed-url for lazy loading
                if not src:
                    src = img.get("data-delayed-url")
                return src
                
        except Exception as e:
            logging.exception(e)
            logging.error("Profile photo not found")
        return None

    def get_background_photo_url(self) -> str or None:
        """Extract background banner image URL"""
        try:
            # Background is usually in a div with background-image style
            banner = self.profile.find(
                "div",
                attrs={"class": lambda x: x and "profile-background-image" in x}
            )
            
            if banner:
                style = banner.get("style", "")
                # Extract URL from style="background-image: url('...')"
                match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                if match:
                    return match.group(1)
                    
        except Exception as e:
            logging.exception(e)
            logging.error("Background photo not found")
        return None

    def get_profile_metadata(self) -> Dict:
        """Extract profile metadata like connections and followers"""
        metadata = {
            "connectionCount": None,
            "followerCount": None,
            "isPremium": False,
            "isOpenToWork": False,
            "isHiring": False
        }
        
        try:
            # Connection count
            conn_elem = self.profile.find(
                "span",
                attrs={"class": "t-bold"}
            )
            if conn_elem and "connection" in conn_elem.parent.text.lower():
                conn_text = conn_elem.text.strip()
                # Parse "500+" or "1,234"
                conn_text = conn_text.replace(",", "").replace("+", "")
                try:
                    metadata["connectionCount"] = int(conn_text)
                except:
                    metadata["connectionCount"] = conn_text
            
            # Follower count
            follower_elems = self.profile.find_all("span", attrs={"class": "t-bold"})
            for elem in follower_elems:
                parent_text = elem.parent.text.lower()
                if "follower" in parent_text:
                    follower_text = elem.text.strip().replace(",", "")
                    try:
                        metadata["followerCount"] = int(follower_text)
                    except:
                        metadata["followerCount"] = follower_text
                    break
            
            # Premium badge
            premium_badge = self.profile.find(
                "span",
                attrs={"class": lambda x: x and "premium" in x.lower()}
            )
            metadata["isPremium"] = premium_badge is not None
            
            # Open to work badge
            open_to_work = self.profile.find(
                "span",
                text=lambda x: x and "Open to work" in x
            )
            metadata["isOpenToWork"] = open_to_work is not None
            
            # Hiring badge
            hiring = self.profile.find(
                "span",
                text=lambda x: x and "Hiring" in x
            )
            metadata["isHiring"] = hiring is not None
            
        except Exception as e:
            logging.error(f"Error getting profile metadata: {e}")
        
        return metadata

    def get_metadata(self) -> dict:
        temp = self.profile.find_all("span", attrs={"class": "pvs-navigation__text"})

        s = "".join(i.text for i in temp)

        store = {
            0: "experience",
            1: "education",
            2: "volunteering_experience",
            3: "skills",
            4: "certifications",
            5: "projects",
            6: "honors",
            7: "publications",
            8: "languages",
        }
        metadata = {
            "sectionExists": {
                "experience": False,
                "education": False,
                "volunteering_experience": False,
                "skills": False,
                "certifications": False,
                "projects": False,
                "honors": False,
                "publications": False,
                "languages": False,
                "courses": False,
            },
            "showAllButtonExists": {
                "experience": False,
                "education": False,
                "volunteering_experience": False,
                "skills": False,
                "certifications": False,
                "projects": False,
                "honors": False,
                "publications": False,
                "languages": False,
            },
        }
        patterns = [
            r"Show all \d+ experiences",
            r"Show all \d+ education",
            r"Show all \d+ volunteer experiences",
            r"Show all \d+ skills",
            r"Show all \d+ certificates?",
            r"Show all \d+ projects?",
            r"Show all \d+ honors?",
            r"Show all \d+ publications?",
            r"Show all \d+ languages?",
        ]
        for idx, pattern in enumerate(patterns):
            if re.search(pattern, s):
                metadata["showAllButtonExists"][store[idx]] = True

        # Check for section existence
        sections_to_check = [
            ("experience", "experience"),
            ("education", "education"),
            ("volunteering_experience", "volunteer"),
            ("skills", "skills"),
            ("certifications", "licenses_and_certifications"),
            ("projects", "projects"),
            ("honors", "honors"),
            ("publications", "publications"),
            ("languages", "languages"),
            ("courses", "courses"),
        ]
        
        for key, div_id in sections_to_check:
            temp_elem = self.profile.find("div", attrs={"id": div_id})
            if temp_elem:
                metadata["sectionExists"][key] = True
            # Also check alternative IDs
            if not temp_elem and key == "honors":
                temp_elem = self.profile.find("div", attrs={"id": "honors_and_awards"})
                if temp_elem:
                    metadata["sectionExists"][key] = True

        return metadata

    def get_experience(self) -> List:
        experience_list = []
        if self.metadata["showAllButtonExists"]["experience"]:
            self.driver.get(self.url + "details/experience/")
            time.sleep(2)

            experience = self.driver.page_source
            experience = bs(experience, "lxml")

            experience = self.get_lists(experience)

            logging.debug("experience page loaded...")
        else:
            experience = self.profile.find("div", attrs={"id": "experience"}).parent
            experience = experience.find("ul").find_all(
                "li",
                attrs={
                    "class": "artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column"
                },
            )
            logging.debug("using profile page...")

        for exp in experience:
            experience_dict = self.get_dict("experience")

            temp = exp.find(
                "div", attrs={"class": "display-flex flex-row justify-space-between"}
            ).find_all("span", attrs={"class": "visually-hidden"})

            ### TITLE ###
            experience_dict["title"] = self.clean_text(temp[0].text)

            ### COMPANY ###
            company = temp[1].text
            company = company.replace(" ", "").split("·")
            if len(company) == 2:
                experience_dict["company"] = self.clean_text(company[0])
                experience_dict["employmentType"] = self.clean_text(company[1])

            if len(company) == 1:
                if company[0] in [
                    "Full-time",
                    "Part-time",
                    "Self-employed",
                    "Freelance",
                    "Internship",
                    "Trainee",
                ]:
                    experience_dict["employmentType"] = self.clean_text(company[0])
                else:
                    experience_dict["company"] = self.clean_text(company[0])

            ### DURATION ###
            if len(temp) > 2:
                duration = temp[2].text
                duration = duration.replace(" ", "").split("·")
                start_end = duration[0].split("-")
                experience_dict["startDate"] = self.clean_text(start_end[0])
                experience_dict["endDate"] = self.clean_text(start_end[1])
                experience_dict["duration"] = self.clean_text(duration[1]) if len(duration) > 1 else None

                ### LOCATION ###
                if len(temp) > 3:
                    location = temp[3].text
                    location = location.replace(" ", "").split("·")

                    # if both locationType and location are present
                    if len(location) == 2:
                        experience_dict["location"] = self.clean_text(location[0])
                        experience_dict["locationType"] = self.clean_text(location[1])

                    ### taken care of the case where one of the locationType or location is not present
                    if len(location) == 1:
                        if location[0] in ["Remote", "On-site", "Hybrid"]:
                            experience_dict["locationType"] = self.clean_text(location[0])
                        else:
                            experience_dict["location"] = self.clean_text(location[0])

            experience_list.append(experience_dict)

        return experience_list

    def get_education(self) -> List:
        education_list = []

        if self.metadata["showAllButtonExists"]["education"]:
            self.driver.get(self.url + "details/education/")
            time.sleep(2)

            education = self.driver.page_source
            education = bs(education, "lxml")

            education = self.get_lists(education)
            logging.debug("education page loaded...")

        else:
            education = self.profile.find("div", attrs={"id": "education"}).parent
            education = education.find("ul").find_all(
                "li",
                attrs={
                    "class": "artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column"
                },
            )
            logging.debug("using profile page...")

        for edu in education:
            education_dict = self.get_dict("education")

            temp = edu.find(
                "div", attrs={"class": "display-flex flex-row justify-space-between"}
            ).find_all("span", attrs={"class": "visually-hidden"})

            ### SCHOOL ###
            education_dict["school"] = self.clean_text(temp[0].text)

            if len(temp) == 3:
                ### DEGREE ###
                temp1 = temp[1].text
                temp1 = temp1.split(",")
                if len(temp1) == 1:
                    education_dict["degree"] = self.clean_text(temp1[0])
                else:
                    education_dict["degree"] = self.clean_text(temp1[0])
                    education_dict["fieldOfStudy"] = self.clean_text(temp1[1])

                ### DURATION ###
                duration = temp[2].text
                duration = duration.split("-")
                education_dict["startDate"] = self.clean_text(duration[0])
                education_dict["endDate"] = self.clean_text(duration[1])
                try:
                    education_dict["duration"] = abs(
                        int(duration[0].replace(" ", ""))
                        - int(duration[1].replace(" ", ""))
                    )
                except Exception as e:
                    logging.error(e)
                    logging.error("start date and end date not in required format")

            elif len(temp) == 2:
                # Now we have to check if the first element is degree or duration
                pattern = re.compile(r"\d{4}\s-\s\d{4}")
                match = re.findall(pattern, temp[1].text)
                if len(match) == 0:
                    # this means that the first element is degree
                    temp1 = temp[1].text
                    temp1 = temp1.split(",")
                    if len(temp1) == 1:
                        education_dict["degree"] = self.clean_text(temp1[0])
                    else:
                        education_dict["degree"] = self.clean_text(temp1[0])
                        education_dict["fieldOfStudy"] = self.clean_text(temp1[1])
                else:
                    # this means that the first element is duration
                    duration = temp[1].text
                    duration = duration.split("-")
                    education_dict["startDate"] = self.clean_text(duration[0])
                    education_dict["endDate"] = self.clean_text(duration[1])
                    try:
                        education_dict["duration"] = abs(
                            int(duration[0].replace(" ", ""))
                            - int(duration[1].replace(" ", ""))
                        )
                    except Exception as e:
                        logging.error(e)
                        logging.error("start date and end date not in required format")
            education_list.append(education_dict)

        return education_list

    def get_volunteering(self) -> List:
        volunteer_list = []
        if self.metadata["showAllButtonExists"]["volunteering_experience"]:
            self.driver.get(self.url + "details/volunteering-experiences/")
            time.sleep(2)

            volunteer = self.driver.page_source
            volunteer = bs(volunteer, "lxml")
            volunteer = self.get_lists(volunteer)
            logging.debug("volunteer page loaded...")
        else:
            volunteer = self.profile.find("div", attrs={"id": "volunteer"}).parent
            volunteer = volunteer.find("ul").find_all(
                "li",
                attrs={
                    "class": "artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column"
                },
            )
            logging.debug("using profile page...")

        for vol in volunteer:
            volunteer_dict = self.get_dict("volunteering")

            temp = vol.find(
                "div", attrs={"class": "display-flex flex-row justify-space-between"}
            ).find_all("span", attrs={"class": "visually-hidden"})

            if len(temp) >= 1:
                volunteer_dict["role"] = self.clean_text(temp[0].text)

            if len(temp) >= 2:
                volunteer_dict["organisation"] = self.clean_text(temp[1].text)

            if len(temp) == 3:
                pattern = re.compile(r"\d{4}\s-\s\d{4}")
                match = re.findall(pattern, temp[2].text)
                if len(match) != 0:
                    ### DURATION ###
                    duration = temp[2].text
                    duration = duration.replace(" ", "").split("·")
                    start_end = duration[0].split("-")
                    volunteer_dict["startDate"] = self.clean_text(start_end[0])
                    volunteer_dict["endDate"] = self.clean_text(start_end[1])
                    volunteer_dict["duration"] = self.clean_text(duration[1]) if len(duration) > 1 else None
                else:
                    volunteer_dict["cause"] = self.clean_text(temp[2].text)
            elif len(temp) >= 4:
                ### DURATION ###
                duration = temp[2].text
                duration = duration.replace(" ", "").split("·")
                start_end = duration[0].split("-")
                volunteer_dict["startDate"] = self.clean_text(start_end[0])
                volunteer_dict["endDate"] = self.clean_text(start_end[1])
                volunteer_dict["duration"] = self.clean_text(duration[1]) if len(duration) > 1 else None

                volunteer_dict["cause"] = self.clean_text(temp[3].text)

            volunteer_list.append(volunteer_dict)

        return volunteer_list

    # TODO: not all the skills are visible in one go, so we need to click on the show more button or scroll down sometimes.
    def get_skills(self) -> List:
        skills_list = []

        if self.metadata["showAllButtonExists"]["skills"]:
            self.driver.get(self.url + "details/skills/")
            time.sleep(2)

            skills = self.driver.page_source
            skills = bs(skills, "lxml")

            skills = self.get_lists(skills)
            logging.debug("skills page loaded...")
        else:
            skills = self.profile.find("div", attrs={"id": "skills"}).parent
            skills = skills.find("ul").find_all(
                "li",
                attrs={
                    "class": "artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column"
                },
            )
            logging.debug("using profile page...")

        for skill in skills:
            skill_dict = self.get_dict("skills")

            temp = (
                skill.find(
                    "div",
                    attrs={"class": "display-flex flex-row justify-space-between"},
                )
                .find("span", attrs={"class": "visually-hidden"})
                .text
            )

            skill_dict["skill"] = self.clean_text(temp)

            skills_list.append(skill_dict)

        return skills_list

    def get_certifications(self) -> List[Dict]:
        """Extract certifications and licenses"""
        certifications_list = []
        
        # Check if certifications section exists
        cert_section = self.profile.find(
            "div", 
            attrs={"id": "licenses_and_certifications"}
        )
        
        if not cert_section:
            logging.debug("No certifications section found")
            return [self.get_dict("certification")]
        
        # Check if "Show all" button exists
        if self.metadata["showAllButtonExists"].get("certifications", False):
            # Navigate to detail page
            self.driver.get(self.url + "details/certifications/")
            time.sleep(2)
            
            cert_html = self.driver.page_source
            cert_soup = bs(cert_html, "lxml")
            
            certifications = self.get_lists(cert_soup)
            logging.debug("Certifications detail page loaded")
        else:
            # Parse from main profile
            try:
                certifications = cert_section.parent.find("ul").find_all(
                    "li",
                    attrs={"class": "artdeco-list__item pvs-list__item--line-separated"}
                )
                logging.debug("Using profile page for certifications")
            except:
                return [self.get_dict("certification")]
        
        if not certifications:
            return [self.get_dict("certification")]
        
        for cert in certifications:
            cert_dict = self.get_dict("certification")
            
            try:
                # Get all visually-hidden spans
                spans = cert.find_all("span", attrs={"class": "visually-hidden"})
                
                if len(spans) >= 2:
                    # Certificate name
                    cert_dict["name"] = self.clean_text(spans[0].text)
                    
                    # Issuer
                    cert_dict["issuer"] = self.clean_text(spans[1].text)
                    
                    # Dates (if present)
                    if len(spans) >= 3:
                        date_text = self.clean_text(spans[2].text)
                        # Parse: "Issued Mar 2023 · Expires Mar 2026"
                        date_parts = date_text.split("·")
                        
                        for part in date_parts:
                            part = part.strip()
                            if "Issued" in part:
                                cert_dict["issueDate"] = part.replace("Issued", "").strip()
                            elif "Expires" in part:
                                cert_dict["expirationDate"] = part.replace("Expires", "").strip()
                            elif "No Expiration" in part:
                                cert_dict["expirationDate"] = "No Expiration"
                    
                    # Credential ID (if present)
                    if len(spans) >= 4:
                        cred_info = self.clean_text(spans[3].text)
                        if "Credential ID" in cred_info:
                            cert_dict["credentialId"] = cred_info.replace("Credential ID", "").strip()
                    
                    # Try to find credential URL
                    link = cert.find("a", attrs={"class": "optional-action-target-wrapper"})
                    if link:
                        cert_dict["credentialUrl"] = link.get("href", "")
                        
            except Exception as e:
                logging.error(f"Error parsing certification: {e}")
            
            certifications_list.append(cert_dict)
        
        return certifications_list

    def get_projects(self) -> List[Dict]:
        """Extract projects"""
        projects_list = []
        
        # Check for projects section
        projects_section = self.profile.find("div", attrs={"id": "projects"})
        
        if not projects_section:
            logging.debug("No projects section found")
            return [self.get_dict("project")]
        
        # Check for "Show all" button
        if self.metadata["showAllButtonExists"].get("projects", False):
            self.driver.get(self.url + "details/projects/")
            time.sleep(2)
            projects_html = self.driver.page_source
            projects_soup = bs(projects_html, "lxml")
            projects = self.get_lists(projects_soup)
        else:
            try:
                projects = projects_section.parent.find("ul").find_all(
                    "li",
                    attrs={"class": "artdeco-list__item pvs-list__item--line-separated"}
                )
            except:
                return [self.get_dict("project")]
        
        if not projects:
            return [self.get_dict("project")]
        
        for proj in projects:
            project_dict = self.get_dict("project")
            
            try:
                spans = proj.find_all("span", attrs={"class": "visually-hidden"})
                
                if len(spans) >= 1:
                    # Project name
                    project_dict["name"] = self.clean_text(spans[0].text)
                
                if len(spans) >= 2:
                    # Date range or associated entity
                    text = self.clean_text(spans[1].text)
                    if "-" in text and any(char.isdigit() for char in text):
                        # Looks like a date range
                        date_parts = text.split("-")
                        if len(date_parts) == 2:
                            project_dict["startDate"] = date_parts[0].strip()
                            project_dict["endDate"] = date_parts[1].strip()
                    else:
                        # Associated with
                        project_dict["associatedWith"] = text
                
                if len(spans) >= 3:
                    # Could be associated with or description
                    text = self.clean_text(spans[2].text)
                    if not project_dict["associatedWith"]:
                        project_dict["associatedWith"] = text
                
                # Description (usually in a separate div)
                desc_div = proj.find(
                    "div",
                    attrs={"class": lambda x: x and "display-flex" in x}
                )
                if desc_div:
                    desc_span = desc_div.find("span", attrs={"aria-hidden": "true"})
                    if desc_span:
                        project_dict["description"] = self.clean_text(desc_span.text)
                
                # Project URL
                link = proj.find("a", href=True)
                if link and "http" in link.get("href", ""):
                    project_dict["url"] = link["href"]
                    
            except Exception as e:
                logging.error(f"Error parsing project: {e}")
            
            projects_list.append(project_dict)
        
        return projects_list

    def get_publications(self) -> List[Dict]:
        """Extract publications"""
        publications_list = []
        
        pub_section = self.profile.find("div", attrs={"id": "publications"})
        
        if not pub_section:
            logging.debug("No publications section found")
            return [self.get_dict("publication")]
        
        if self.metadata["showAllButtonExists"].get("publications", False):
            self.driver.get(self.url + "details/publications/")
            time.sleep(2)
            pub_html = self.driver.page_source
            pub_soup = bs(pub_html, "lxml")
            publications = self.get_lists(pub_soup)
        else:
            try:
                publications = pub_section.parent.find("ul").find_all(
                    "li",
                    attrs={"class": "artdeco-list__item pvs-list__item--line-separated"}
                )
            except:
                return [self.get_dict("publication")]
        
        if not publications:
            return [self.get_dict("publication")]
        
        for pub in publications:
            pub_dict = self.get_dict("publication")
            
            try:
                spans = pub.find_all("span", attrs={"class": "visually-hidden"})
                
                if len(spans) >= 1:
                    pub_dict["title"] = self.clean_text(spans[0].text)
                
                if len(spans) >= 2:
                    # Publisher and date are often combined
                    info = self.clean_text(spans[1].text)
                    parts = info.split(",")
                    if len(parts) >= 1:
                        pub_dict["publisher"] = parts[0].strip()
                    if len(parts) >= 2:
                        pub_dict["publicationDate"] = parts[1].strip()
                
                # Description
                if len(spans) >= 3:
                    pub_dict["description"] = self.clean_text(spans[2].text)
                
                # URL
                link = pub.find("a", href=True)
                if link and "http" in link.get("href", ""):
                    pub_dict["url"] = link["href"]
                    
            except Exception as e:
                logging.error(f"Error parsing publication: {e}")
            
            publications_list.append(pub_dict)
        
        return publications_list

    def get_languages(self) -> List[Dict]:
        """Extract languages"""
        languages_list = []
        
        lang_section = self.profile.find("div", attrs={"id": "languages"})
        
        if not lang_section:
            logging.debug("No languages section found")
            return [self.get_dict("language")]
        
        if self.metadata["showAllButtonExists"].get("languages", False):
            self.driver.get(self.url + "details/languages/")
            time.sleep(2)
            lang_html = self.driver.page_source
            lang_soup = bs(lang_html, "lxml")
            languages = self.get_lists(lang_soup)
        else:
            try:
                languages = lang_section.parent.find("ul").find_all(
                    "li",
                    attrs={"class": "artdeco-list__item pvs-list__item--line-separated"}
                )
            except:
                return [self.get_dict("language")]
        
        if not languages:
            return [self.get_dict("language")]
        
        for lang in languages:
            lang_dict = self.get_dict("language")
            
            try:
                spans = lang.find_all("span", attrs={"class": "visually-hidden"})
                
                if len(spans) >= 1:
                    lang_dict["language"] = self.clean_text(spans[0].text)
                
                if len(spans) >= 2:
                    # Proficiency level
                    lang_dict["proficiency"] = self.clean_text(spans[1].text)
                    
            except Exception as e:
                logging.error(f"Error parsing language: {e}")
            
            languages_list.append(lang_dict)
        
        return languages_list

    def get_honors(self) -> List[Dict]:
        """Extract honors and awards"""
        honors_list = []
        
        honors_section = self.profile.find("div", attrs={"id": "honors"})
        if not honors_section:
            honors_section = self.profile.find("div", attrs={"id": "honors_and_awards"})
        
        if not honors_section:
            logging.debug("No honors section found")
            return [self.get_dict("honor")]
        
        if self.metadata["showAllButtonExists"].get("honors", False):
            self.driver.get(self.url + "details/honors/")
            time.sleep(2)
            honors_html = self.driver.page_source
            honors_soup = bs(honors_html, "lxml")
            honors = self.get_lists(honors_soup)
        else:
            try:
                honors = honors_section.parent.find("ul").find_all(
                    "li",
                    attrs={"class": "artdeco-list__item pvs-list__item--line-separated"}
                )
            except:
                return [self.get_dict("honor")]
        
        if not honors:
            return [self.get_dict("honor")]
        
        for honor in honors:
            honor_dict = self.get_dict("honor")
            
            try:
                spans = honor.find_all("span", attrs={"class": "visually-hidden"})
                
                if len(spans) >= 1:
                    honor_dict["title"] = self.clean_text(spans[0].text)
                
                if len(spans) >= 2:
                    # Issuer
                    honor_dict["issuer"] = self.clean_text(spans[1].text)
                
                if len(spans) >= 3:
                    # Date
                    honor_dict["date"] = self.clean_text(spans[2].text)
                
                if len(spans) >= 4:
                    # Description
                    honor_dict["description"] = self.clean_text(spans[3].text)
                    
            except Exception as e:
                logging.error(f"Error parsing honor: {e}")
            
            honors_list.append(honor_dict)
        
        return honors_list

    def get_courses(self) -> List[Dict]:
        """Extract courses"""
        courses_list = []
        
        courses_section = self.profile.find("div", attrs={"id": "courses"})
        
        if not courses_section:
            logging.debug("No courses section found")
            return [self.get_dict("course")]
        
        try:
            courses = courses_section.parent.find("ul").find_all(
                "li",
                attrs={"class": "artdeco-list__item pvs-list__item--line-separated"}
            )
        except:
            return [self.get_dict("course")]
        
        if not courses:
            return [self.get_dict("course")]
        
        for course in courses:
            course_dict = self.get_dict("course")
            
            try:
                spans = course.find_all("span", attrs={"class": "visually-hidden"})
                
                if len(spans) >= 1:
                    # Course name and number combined
                    text = self.clean_text(spans[0].text)
                    # Sometimes format is "Course Name · Course Number"
                    if "·" in text:
                        parts = text.split("·")
                        course_dict["name"] = parts[0].strip()
                        if len(parts) > 1:
                            course_dict["number"] = parts[1].strip()
                    else:
                        course_dict["name"] = text
                
                if len(spans) >= 2:
                    # Associated school
                    course_dict["associatedWith"] = self.clean_text(spans[1].text)
                    
            except Exception as e:
                logging.error(f"Error parsing course: {e}")
            
            courses_list.append(course_dict)
        
        return courses_list

    def get_dict(self, type: str) -> Dict:
        temp = {}
        if type == "experience":
            temp = {
                "title": None,
                "company": None,
                "employmentType": None,
                "startDate": None,
                "endDate": None,
                "duration": None,
                "location": None,
                "locationType": None,
            }
        elif type == "education":
            temp = {
                "school": None,
                "degree": None,
                "fieldOfStudy": None,
                "startDate": None,
                "endDate": None,
                "duration": None,
            }
        elif type == "certification":
            temp = {
                "name": None,
                "issuer": None,
                "issueDate": None,
                "expirationDate": None,
                "credentialId": None,
                "credentialUrl": None,
            }
        elif type == "project":
            temp = {
                "name": None,
                "description": None,
                "url": None,
                "startDate": None,
                "endDate": None,
                "associatedWith": None,
            }
        elif type == "publication":
            temp = {
                "title": None,
                "publisher": None,
                "publicationDate": None,
                "description": None,
                "url": None,
            }
        elif type == "language":
            temp = {
                "language": None,
                "proficiency": None,
            }
        elif type == "honor":
            temp = {
                "title": None,
                "issuer": None,
                "date": None,
                "description": None,
            }
        elif type == "course":
            temp = {
                "name": None,
                "number": None,
                "associatedWith": None,
            }
        elif type == "volunteering":
            temp = {
                "role": None,
                "organisation": None,
                "startDate": None,
                "endDate": None,
                "duration": None,
                "cause": None,
            }
        elif type == "skills":
            temp = {
                "skill": None,
            }
        else:
            logging.critical(f"Invalid type: {type}")

        return temp

    def get_lists(self, source: object) -> List:
        try:
            return (
                source.find("main", attrs={"class": "scaffold-layout__main"})
                .find("section", attrs={"class": "artdeco-card ember-view pb3"})
                .find("div", attrs={"class": "pvs-list__container"})
                .find("ul")
                .find_all(
                    "li",
                    attrs={
                        "class": "pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column"
                    },
                )
            )
        except Exception as e:
            logging.exception(e)
            logging.critical(
                "li elements not found... try again or check the class names"
            )
            return None

    def get_json_output(self) -> str:
        """Generate JSON output with all extracted data"""
        data = {
            "url": self.url,
            "name": self.name,
            "headline": self.headline,
            "location": self.location,
            "about": self.about,
            "profilePhotoUrl": self.profile_photo_url,
            "backgroundPhotoUrl": self.background_photo_url,
            "metadata": self.profile_metadata,
            "experience": self.experience,
            "education": self.education,
            "certifications": self.certifications,
            "projects": self.projects,
            "publications": self.publications,
            "languages": self.languages,
            "honors": self.honors,
            "courses": self.courses,
            "volunteering": self.volunteering,
            "skills": self.skills,
        }
        
        # Remove null values for cleaner output
        def remove_nulls(d):
            if isinstance(d, dict):
                return {k: remove_nulls(v) for k, v in d.items() if v is not None and v != [{"skill": None}] and v != [{}]}
            elif isinstance(d, list):
                cleaned_list = [remove_nulls(item) for item in d if item is not None]
                # Filter out empty dicts or dicts with all None values
                cleaned_list = [item for item in cleaned_list if item and any(v is not None for v in item.values())]
                return cleaned_list if cleaned_list else None
            else:
                return d
        
        clean_data = remove_nulls(data)
        
        output = json.dumps(
            clean_data,
            indent=4,
            ensure_ascii=False  # Better for international characters
        )

        return output

    def save_output_in_file(self) -> None:
        if self.save:
            filename = self.url.split("/")[-2]
            try:
                import json

                if not os.path.exists("./data"):
                    os.makedirs("data")
                with open(f"./data/{filename}.json", "w", encoding="utf-8") as f:
                    f.write(self.output)
                    logging.critical(f"File saved as {filename}.json")
            except Exception as e:
                logging.exception(e)
                logging.critical("Error in saving the file")
        else:
            return None