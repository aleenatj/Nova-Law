/** Welcome / intro for section 1 (not part of engage.json). */
export const engageWelcomeContent = {
  title: "Welcome to Nova Engage",
  intro:
    "We will help you take control of your family law journey. Engage will guide you, regardless of whether you are going through separation, divorce or making plans for your relationship through pre-nuptial or post-nuptial arrangements. Engage <strong>is not</strong> suitable if you are a grandparent seeking contact with grandchildren or if you require advice on surrogacy - if this applies to you please check back with your lawyer. Engage is dynamic and will only ask you for information that your family specialist will need to know.",
  subheading: "A few things to bear in mind as you answer our questions-",
  points: [
    {
      text: "Throughout this guided pathway the term <strong>'partner'</strong> will be used to refer to the person you need to communicate with, regardless of marital status or whether the relationship is continuing or has finished.",
    },
    {
      text: "Please answer as many of our questions as possible before submitting. Doing so will allow your lawyer to <strong>better understand</strong> your circumstances, give you the <strong>most accurate advice</strong> and <strong>save you hundreds of pounds</strong> you would have spent giving them the information in person. The more questions you answer, the more comprehensive the advice and the greater the savings.",
    },
    {
      text: "Engage allows you to brief your family specialist <strong>at your own pace</strong>, you aren’t on the lawyer’s clock. We know it can be hard, you may be reliving an uncomfortable part of your life. If you feel you need more time to answer our questions, you can reschedule your appointment. Remember: <strong>your family specialist works for you, so they will understand.</strong>",
    },
    {
      text: "Don’t worry if you don’t have exact information about your partner, you will be able to say so, or provide a guesstimate. The important thing is not to leave sections blank, otherwise your specialist will take up valuable consultation time asking lots of questions. If you are dealing with financial claims or any other finance-related matters, having the following documents to hand will make it easier for you to answer our questions:",
      items: [
        "Bank account details for you, your partner or jointly held.",
        "Details of your family home such as its current market value, mortgage details, date of purchase, etc.",
        "Salary slips for yourself and your partner (if possible).",
        "Details for assets such as other properties or investments owned by you and/or your partner.",
        "Liability details.",
        "Pension details, if possible, for yourself and your partner.",
      ],
    },
  ],
  closing:
    "Finally, if you are seeking legal advice having previously attempted mediation and have been provided with any or all of the following documents, you may be given the option to upload them.<br>CW5, FM1, Memorandum of Understanding, Open Financial Statement, Outcome Summary.<br><br>Question boxes marked with * will need an answer before you can move on from a section.",
};

/** Section 2 welcome — `{name}` replaced with client first name from answers. */
export const engageSection2Welcome = {
  title: "Thank you, {name}",
  intro:
    "<p>Thank you. We appreciate that this can be a very challenging time for you. The questions in this section help us understand your situation so your family specialist can support you effectively.</p><p>Answer as fully as you can. Questions marked with <strong>*</strong> must be completed before you can continue.</p>",
  closing:
    '<p class="text-novaNeutral-600 text-sm">Nova Engage provides legal information to help you prepare for your consultation. It does not constitute legal advice. Your family specialist will advise you based on your individual circumstances.</p>',
};
