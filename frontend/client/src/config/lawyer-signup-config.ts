export const lawyerSignupConfig = {
  "formTitle": "Become a Nova Professional",
  "sections": [
    {
      "id": 1,
      "title": "Personal Information",
      "fields": [
        {
          "id": 24,
          "label": "Eligibility",
          "type": "html"
        },
        {
          "id": 1,
          "label": "Introduce yourself",
          "type": "name",
          "required": true,
          "fields": ["firstName", "lastName"],
          "maxLength": {
            "firstName": 99,
            "lastName": 99
          }
        }
      ]
    },
    {
      "id": 2,
      "title": "Contact Details",
      "fields": [
        {
          "id": 20,
          "label": "Your contact email",
          "type": "email",
          "required": true,
          "confirmation": true,
          "maxLength": 255
        },
        {
          "id": 21,
          "label": "Telephone number",
          "type": "phone",
          "required": true,
          "format": "international",
          "maxLength": 17
        }
      ]
    },
    {
      "id": 3,
      "title": "Professional Status",
      "fields": [
        {
          "id": 39,
          "label": "What is your work status, {firstName}?",
          "type": "radio",
          "required": true,
          "options": [
            "I work for a legal firm - employed",
            "I am a consultant at a legal firm or chambers - self-employed",
            "I am freelance and not attached to any firm or chambers"
          ],
          "maxLength": 100
        },
        {
          "id": 38,
          "label": "What is the name of your firm?",
          "type": "text",
          "required": true,
          "showIf": {
            "field": 39,
            "values": [
              "I work for a legal firm - employed",
              "I am a consultant at a legal firm or chambers - self-employed"
            ]
          },
          "description": "Or your trading name/brand if freelance",
          "maxLength": 200
        },
        {
          "id": 34,
          "label": "Your work locality",
          "type": "address",
          "required": true,
          "fields": ["city", "postcode"],
          "description": "This can be important for some clients",
          "maxLength": {
            "city": 100,
            "postcode": 20
          }
        }
      ]
    },
    {
      "id": 4,
      "title": "Demographics",
      "fields": [
        {
          "id": 31,
          "label": "Would you like to specify your gender?",
          "type": "radio",
          "required": false,
          "options": ["Female", "Male", "Non-Binary", "Prefer not to say"]
        },
        {
          "id": 33,
          "label": "Upload a profile photo if you wish",
          "type": "file",
          "required": false,
          "description": "This will appear on our platform but it's not obligatory.",
          "allowedTypes": ["jpg", "gif", "png", "jpeg", "webp"],
          "maxSize": "5 MB"
        }
      ]
    },
    {
      "id": 5,
      "title": "Professional Qualifications",
      "fields": [
        {
          "id": 23,
          "label": "What is your professional status?",
          "type": "checkbox",
          "required": false,
          "description": "You may have more than one title",
          "options": [
            {value: "SOLICITOR", label: "Solicitor"},
            {value: "BARRISTER", label: "Barrister"},
            {value: "CILEX", label: "Cilex"},
            {value: "LAWYER_MEDIATOR", label: "Lawyer-Mediator"},
            {value: "NON_LAWYER_MEDIATOR", label: "Mediator"},
            {value: "ARBITRATOR", label: "Arbitrator"},
            {value: "DIVORCE_COACH", label: "Divorce Coach"},
            {value: "FAMILY_CONSULTANT", label: "Family Consultant"},
            {value: "OTHER", label: "Other"},
          ]
        },
        {
          "id": 3,
          "label": "Other? Interesting. Please provide a title.",
          "type": "text",
          "required": false,
          "showIf": {
            "field": 23,
            "contains": "Other"
          },
          "maxLength": 100
        }
      ]
    },
    {
      "id": 6,
      "title": "Experience",
      "fields": [
        {
          "id": 4,
          "label": "{firstName} how many years' experience do you have practising family law?",
          "type": "number",
          "required": false,
          "maxLength": 5,
          "min": 0,
          "maxLengthMessage": "Please enter a valid experience"
        }
      ]
    },
    {
      "id": 7,
      "title": "Client Types",
      "fields": [
        {
          "id": 27,
          "label": "Who do you offer services to?",
          "type": "checkbox",
          "required": false,
          "options": [
            {value: "MARRIED_CIVIL_PARTNERS", label: "Married and Civil Partners"},
            {value: "COHABITEES", label: "Cohabitees"},
            {value: "PARENTAL_RELATIONSHIPS", label: "Parental relationships"},
          ]
        }
      ]
    },
    {
      "id": 8,
      "title": "Practice Areas - Married Couples",
      "fields": [
        {
          "id": 9,
          "label": "Tell us more about your services for married couples and civil partners. What are your main areas of practice?",
          "type": "checkbox",
          "required": false,
          "maxSelections": 5,
          "showIf": {
            "field": 27,
            "contains": "MARRIED_CIVIL_PARTNERS"
          },
          "options": [
            { value: "FINANCIAL_CLAIMS", label: "Financial remedy on divorce or separation" },
            { value: "OVERSEAS_FINANCIAL_CLAIMS", label: "Financial remedy after overseas divorce" },
            { value: "CHILD_ARRANGEMENTS", label: "Children (child arrangements)" },
            { value: "CHILDREN_DOMESTIC_RELOCATION", label: "Children (domestic relocation)" },
            { value: "CHILDREN_INTERNATIONAL_RELOCATION", label: "Children (international relocation)" },
            { value: "INHERITANCE_ACT_CLAIMS", label: "Inheritance Act claims" },
            { value: "PRE_NUPTIAL_PRE_CIVIL_PARTNERSHIP_AGREEMENTS", label: "Pre-nuptial & pre-civil partnership agreements" },
            { value: "POST_NUPTIAL_POST_CIVIL_PARTNERSHIP_AGREEMENTS", label: "Post-nuptial and post-civil partnership agreements" },
            { value: "OTHER_MARRIED_CIVIL_PARTNERS", label: "Other" },            
          ]
        }
      ]
    },
    {
      "id": 9,
      "title": "Practice Areas - Cohabitees",
      "fields": [
        {
          "id": 29,
          "label": "Tell us more about your services for cohabitees. What are your main areas of practice?",
          "type": "checkbox",
          "required": false,
          "maxSelections": 5,
          "showIf": {
            "field": 27,
            "contains": "COHABITEES"
          },
          "options": [
            { value: "SEPARATION_AGREEMENTS", label: "Separation agreements" },
            { value: "COHABITATION_CHILD_ARRANGEMENTS", label: "Children (child arrangements)" },
            { value: "COHABITATION_CHILDREN_DOMESTIC_RELOCATION", label: "Children (domestic relocation)" },
            { value: "COHABITATION_CHILDREN_INTERNATIONAL_RELOCATION", label: "Children (international relocation)" },
            { value: "COHABITATION_FINANCIAL_CLAIMS", label: "TOLATA" },
            { value: "LIVING_TOGETHER_AGREEMENTS", label: "Living together agreements" },
            { value: "SCHEDULE_I_CLAIMS", label: "Schedule I claims" },
            { value: "COHABITATION_INHERITANCE_ACT_CLAIMS", label: "Inheritance Act claims" },
            { value: "OTHER_COHABITEES", label: "Other " },            
          ]
        }
      ]
    },
    {
      "id": 9,
      "title": "NCDR Services",
      "fields": [
        {
          "id": 18,
          "label": "Show us your NCDR magic, {firstName}: what can you offer?",
          "type": "checkbox",
          "required": false,
          "options": [
            {
              "DIRECT_NEGOTIATION": {
                  "value": "DIRECT_NEGOTIATION",
                  "label": "Direct Negotiation",
                  "type": "NORMAL",
                  "group": "None",
              },
              "MEDIATION": {
                  "value": "MEDIATION",
                  "label": "Mediation",
                  "type": "NORMAL",
                  "group": "None",
              },
              "ONE_LAWYER_ONE_COUPLE": {
                  "value": "ONE_LAWYER_ONE_COUPLE",
                  "label": "One Lawyer One Couple",
                  "type": "NORMAL",
                  "group": "None",
              },
              "COLLABORATIVE": {
                  "value": "COLLABORATIVE",
                  "label": "Collaborative",
                  "type": "NORMAL",
                  "group": "None",
              },
              "HYBRID_MEDIATION_SUPPORT": {
                  "value": "HYBRID_MEDIATION_SUPPORT",
                  "label": "Hybrid Mediation-Support",
                  "type": "SUPPORT",
                  "group": "Hybrid Mediation",
              },
              "HYBRID_MEDIATION_MEDIATOR": {
                  "value": "HYBRID_MEDIATION_MEDIATOR",
                  "label": "Hybrid Mediation-Mediator",
                  "type": "OTHER",
                  "group": "Hybrid Mediation",
              },
              "LAWYER_NEGOTIATION": {
                  "value": "LAWYER_NEGOTIATION",
                  "label": "Lawyer Negotiation",
                  "type": "NORMAL",
                  "group": "None",
              },
              "EARLY_NEUTRAL_EVALUATION_SUPPORT": {
                  "value": "EARLY_NEUTRAL_EVALUATION_SUPPORT",
                  "label": "Early Neutral Evaluation/Private FDR-Support",
                  "type": "SUPPORT",
                  "group": "Early Neutral Evaluation/Private FDR",
              },
              "EARLY_NEUTRAL_EVALUATION_EVALUATOR": {
                  "value": "EARLY_NEUTRAL_EVALUATION_EVALUATOR",
                  "label": "Early Neutral Evaluation/Private FDR-Evaluator",
                  "type": "OTHER",
                  "group": "Early Neutral Evaluation/Private FDR",
              },
              "ARBITRATION_SUPPORT": {
                  "value": "ARBITRATION_SUPPORT",
                  "label": "Arbitration-Support",
                  "type": "SUPPORT",
                  "group": "Arbitration",
              },
              "ARBITRATION_ARBITRATOR": {
                  "value": "ARBITRATION_ARBITRATOR",
                  "label": "Arbitration-Arbitrator",
                  "type": "OTHER",
                  "group": "Arbitration",
              },
              "COURT": {
                  "value": "COURT",
                  "label": "Court",
                  "type": "NORMAL",
                  "group": "None",
              },
          }
          ]
        }
      ]
    },
    {
      "id": 10,
      "title": "Accreditations",
      "fields": [
        {
          "id": 19,
          "label": "Are you an accredited specialist?",
          "type": "checkbox",
          "required": false,
          "options": [
            {value: "RESOLUTION_ACCREDITED_SPECIALIST", label: "Resolution Accredited Specialist"},
            {value: "LAW_SOCIETY_ACCREDITED_SPECIALIST", label: "Law Society Accredited Specialist"},
            {value: "FMC_ACCREDITED_MEDIATOR", label: "FMC Accredited Mediator"},
            {value: "CIARB_ACCREDITED_ARBITRATOR", label: "CIArb Accredited Arbitrator"},
            {value: "OTHER", label: "Other"},
          ],
          "description": "Tick any that apply."
        },
        {
          "id": 47,
          "label": "Other? Please provide your accredited specialism",
          "type": "text",
          "required": false,
          "maxLength": 100,
          "showIf": {
            "field": 19,
            "value": "OTHER"
          }
        },
        {
          "id": 40,
          "label": "Please select your regulator",
          "type": "radio",
          "required": false,
          "options": [
            {value: "SRA", label: "Solicitors Regulation Authority"},
            {value: "BSB", label: "Bar Standards Board"},
            {value: "CILEX", label: "Cilex Regulation"},
            {value: "OTHER", label: "Other"},
          ]
        },
        {
          "id": 46,
          "label": "Other? Interesting. Please provide your regulator",
          "type": "text",
          "required": false,
          "maxLength": 100,
          "showIf": {
            "field": 40,
            "value": "OTHER"
          }
        }
      ]
    },
    {
      "id": 11,
      "title": "Profile Information",
      "fields": [
        {
          "id": 11,
          "label": "Do you share our passion for NCDR? What should potential clients know about you?",
          "type": "textarea",
          "required": false,
          "maxLength": 400,
          "description": "Tip: this content will appear in your nova profile, Write in first person, short and sweet, to increase the impact for your potential clients. Click on the contextual help to see some examples.",
          "contextualHelp": "<p><strong>Example 1: </strong></p><p>The best part of my role as a mediator is helping my clients work out their own solutions to their dispute.  I never get tired of seeing that look on their faces that says: \'That was hard but we did it!\'</p><p> </p><p><strong>Example 2</strong></p><p>I enjoy working with clients using the collaborative law model.  It is very powerful to see a couple work through their challenges at a pace that suits them.  I think my clients appreciate the fact that there is no judge telling them and their partner what to do or hurrying them along.  In collaborative practice, I carefully listen to my clients and their partners to find the answers the family needs.</p>"
        }
      ]
    },
    {
      "id": 12,
      "title": "Profile Information",
      "fields": [
        {
          "id": 14,
          "label": "Give us a compelling quote from one of your clients.",
          "type": "textarea",
          "required": false,
          "maxLength": 400,
          "description": "It's not obligatory but your potential clients will find it helpfull."
        }
      ]
    },
    {
      "id": 13,
      "title": "Service Delivery",
      "fields": [
        {
          "id": 37,
          "label": "If requested, do you offer remote client consultations, {firstName}?",
          "type": "radio",
          "required": false,
          "options": ["Yes", "No"],
          "description": "Zoom, Teams, FaceTime etc."
        }
        // {
        //   "id": 36,
        //   "label": "First Meetings. What can you offer clients?",
        //   "type": "checkbox",
        //   "required": false,
        //   "options": [
        //     {value: "FREE_INITIAL_INTERVIEW", label: "Free initial interview"},
        //     {value: "FIXED_FEE_INITIAL_INTERVIEW", label: "Fixed fee initial interview"},
        //     {value: "HOURLY_RATE_INITIAL_INTERVIEW", label: "Hourly rate initial interview"},
        //     {value: "LEGAL_AID_LEGAL_HELP_INTERVIEW", label: "Legal Aid/Legal Help interview"},
        //   ],
        //   "description": "Tick any that apply."
        // }
      ]
    }
  ],
  "notifications": {
    "admin": ["Alan@novalaw.co.uk", "Sam@novalaw.co.uk"],
    "userConfirmation": "Thank you email sent from Alan@novalaw.co.uk"
  },
  "confirmationMessage": "Thank you for contacting us.",
  "privacyNote": "We respect your confidentiality and will never contact anyone without your specific consent."
}