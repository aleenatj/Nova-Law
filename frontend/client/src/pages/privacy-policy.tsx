import React from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";

const PrivacyPolicy: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <LandingHeader hidenavs={false}/>
      <main id="main-content" role="main" className="flex-1 bg-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-8 text-center font-nineties tracking-wide">
            Privacy Policy
          </h1>
          
          <div className="prose prose-lg max-w-none">
            <div className="text-novaNeutral-600 space-y-6">
              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">BACKGROUND</h2>
                <p className="mb-4">
                  Nova understands that your privacy is important to you and that you care about how your personal data is used. We respect and value the privacy of everyone who visits our websites at <a href="https://novalaw.co.uk" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">https://novalaw.co.uk</a> and <a href="https://novaforprofessionals.novalaw.co.uk" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">https://novaforprofessionals.novalaw.co.uk</a> collectively known as "Our Site" and will only collect and use personal data in ways that are described here, and in a way that is consistent with our obligations and your rights under the UK General Data Protection Regulation ("GDPR") and the Data Protection Act 2018 ("DPA'18") jointly referred to as "Data Protection Legislation".
                </p>
                <p className="mb-4">
                  Please read this Privacy Policy carefully and ensure that you understand it.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">1. Definitions and Interpretation</h2>
                <div className="ml-6">
                  <p className="mb-4">In this Policy the following terms shall have the following meanings:</p>
                  <table className="min-w-full border border-gray-300">
                    <tbody>
                      <tr>
                        <td className="font-semibold border border-gray-300 px-4 py-2">"Account"</td>
                        <td className="border border-gray-300 px-4 py-2">means an account required to access and/or use certain areas and features of Our Site;</td>
                      </tr>
                      <tr>
                        <td className="font-semibold border border-gray-300 px-4 py-2">"General Visitor(s)"</td>
                        <td className="border border-gray-300 px-4 py-2">means a visitor to Our Site other than defined below as a "Nova Platform User".</td>
                      </tr>
                      <tr>
                        <td className="font-semibold border border-gray-300 px-4 py-2">"Nova Platform"</td>
                        <td className="border border-gray-300 px-4 py-2">Means a web-based platform hosting software, automated systems, algorithms, generative artificial intelligence or other technologies that help deliver, personalize, or improve the services on Our Site.</td>
                      </tr>
                      <tr>
                        <td className="font-semibold border border-gray-300 px-4 py-2">"Nova Applications"</td>
                        <td className="border border-gray-300 px-4 py-2">Means a collective term for the web-based services on the Nova Platform available to Nova Platform Users.</td>
                      </tr>
                      <tr>
                        <td className="font-semibold border border-gray-300 px-4 py-2">"Nova Platform User(s)"</td>
                        <td className="border border-gray-300 px-4 py-2">means a member of the public, most likely a current or potential client of a law firm wishing to access Nova Applications including, but not limited to, our client onboarding application called "Nova Engage".</td>
                      </tr>
                      <tr>
                        <td className="font-semibold border border-gray-300 px-4 py-2">"Law Firms"</td>
                        <td className="border border-gray-300 px-4 py-2">A law firm who contracts with Nova to use the Nova Platform.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">2. Information About Us</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">2.1</strong> Our Site is owned and operated by Nova Law Trading Limited, a legal services technology company registered in England under company number 14139589 ("Nova").
                  </p>
                  <p className="mb-2">Registered address: Preston Park House, South Road, Brighton BN1 6SB.</p>
                  <p className="mb-2">Data Protection Officer: Alan Larkin.</p>
                  <p className="mb-2 ml-8">Email address: <a href="mailto:alan@novalaw.co.uk" className="text-blue-600 underline hover:text-blue-800">alan@novalaw.co.uk</a>.</p>
                  <p className="mb-2 ml-8">Telephone number: 01273 077126.</p>
                  <p className="mb-4 ml-8">Postal address: 5 Clifton Mews, Clifton Hill, Brighton, BN1 3HR.</p>
                  <p className="mb-4">
                    <strong className="mr-1">2.2</strong> Nova's Privacy Policy is set out below in relation to the generality of Our Site. Nova facilitates services for members of the public who arrive directly at this site and are defined above as "General Visitor(s)". General Visitors who access Nova Applications on Our Site will be defined as "Nova Platform Users". Additionally, Nova facilitates services for selected law firms and individuals introduced by selected law firms defined above as "Law Firms". Those visitors introduced by such Law Firms will fall under the definition of "Nova Platform Users".
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">2.3</strong> For the purposes of Data Protection Legislation, Nova is the data controller in relation to all personal data collected on Our Site.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">3. What Does This Policy Cover?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">3.1</strong> This Privacy Policy applies to your use of Our Site, whether you are a General Visitor a Nova Platform User or a Law Firm. Our Site may contain links to other websites. Please note that we have no control over how your data is collected, stored, or used by other websites and we advise you to check the privacy policies of any such websites before providing any data to them.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">4. What Data Do We Collect and How?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">4.1</strong> Depending upon your use of Our Site, we may collect and hold some or all of the personal and non-personal data set out in the table below, using the methods also set out in the table. We have broken this down, depending on the type of user below:
                  </p>
                  
                  <div className="mb-6">
                    <h3 className="text-base font-semibold text-novaNeutral-900 mb-3">General Visitors:</h3>
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full border border-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="border border-gray-300 px-4 py-2 text-left">Data Collected, Includes, But Is Not Limited To</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">How We Collect the Data</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">
                              <ul className="list-disc list-inside space-y-1">
                                <li>Name</li>
                                <li>Address</li>
                                <li>Email address</li>
                                <li>Phone number</li>
                              </ul>
                            </td>
                            <td className="border border-gray-300 px-4 py-2">
                              <ul className="list-none list-inside space-y-1">
                                <li>Our contact request form</li>
                                <li>When you may start to fill out a form on Our Site</li>
                              </ul>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="text-base font-semibold text-novaNeutral-900 mb-3">Nova Platform Users:</h3>
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full border border-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="border border-gray-300 px-4 py-2 text-left">Data Collected, Includes, But Is Not Limited To</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">How We Collect the Data</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">
                              <ul className="list-disc list-outside space-y-1 pl-5">
                                <li>Name</li>
                                <li>Address</li>
                                <li>Email address</li>
                                <li>Phone number</li>
                                <li>Date of birth</li>
                                <li>Gender</li>
                                <li>Nationality</li>
                                <li>Information relating to partner (name, gender, telephone number, email address, date of birth, nationality, solicitors used)</li>
                                <li>Information relating to any domestic abuse</li>
                                <li>Information relating to children (name, gender, date of birth, health/special needs, disabilities, education)</li>
                                <li>Opportunities to upload documents and add free text</li>
                                <li>Family home</li>
                                <li>Mortgage</li>
                                <li>Bank accounts</li>
                                <li>Investments</li>
                                <li>Business interests</li>
                                <li>Liabilities</li>
                                <li>Pension funds</li>
                                <li>Work/job</li>
                                <li>Other income sources</li>
                                <li>Health conditions</li>
                                <li>Menopause/perimenopause</li>
                                <li>Inherited wealth</li>
                                <li>Mental health</li>
                                <li>Special assistance needed at offices</li>
                                <li>Criminal offences</li>
                              </ul>
                            </td>
                            <td className="border border-gray-300 px-4 py-2">
                              Specific functionality including, but not limited to, our Nova Applications
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="text-base font-semibold text-novaNeutral-900 mb-3">Law Firms:</h3>
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full border border-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="border border-gray-300 px-4 py-2 text-left">Data Collected, Includes, But Is Not Limited To</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">How We Collect the Data</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">
                              <ul className="list-disc list-inside space-y-1">
                                <li>Key Contact Name</li>
                                <li>Business name</li>
                                <li>Address</li>
                                <li>Email address</li>
                                <li>Profession</li>
                                <li>Payment details</li>
                              </ul>
                            </td>
                            <td className="border border-gray-300 px-4 py-2">
                              <ul className="list-none list-inside space-y-1">
                                <li>Our contact request form</li>
                                <li>Onboarding process via Nova Applications including, but not limited to, Nova Engage</li>
                              </ul>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <p className="mb-4">
                    <strong className="mr-1">4.2</strong> We may also collect the following technical information about your device when you use Our Site. This information helps us ensure the security and proper functioning of our services and to improve their performance.
                  </p>
                  <p className="mb-2">The technical information we collect may include:</p>
                  <ul className="list-disc list-outside space-y-2 ml-4 mb-4 pl-6">
                    <li><strong>Device and browser data:</strong> such as your device type, operating system, browser type and version, screen resolution, language settings, and time zone.</li>
                    <li><strong>Connection data:</strong> such as your Internet Protocol (IP) address, network type (e.g. Wi-Fi, mobile), and referring or exit pages.</li>
                    <li><strong>Usage data:</strong> such as the pages you visit, time spent on each page, links you click, scrolling behaviour, and error or performance logs.</li>
                  </ul>
                  <p className="mb-4">
                    We collect this information automatically through our servers and similar technologies (for example, server logs and security monitoring tools).
                  </p>
                  <p className="mb-4">
                    Where this information could identify you (for example, your IP address), we treat it as <strong>personal data</strong> in accordance with applicable data protection laws.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">5. Special Category and Minor's Data</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">5.1</strong> As highlighted above, during the course of using Our Site Nova Platform Users may disclose special category personal data including, but not limited to, racial and ethnic origin, religious or philosophical beliefs and health or sexual orientation.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">5.2</strong> It may also be necessary, in some circumstances, to collect information about children and minors, defined under Data Protection Legislation as individuals who are below the age of 13.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">5.3</strong> Nova shall ensure that additional safeguards are in place to protect such special category and sensitive data, such as information collected in relation to children.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">6. How Do You Use My Personal Data?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">6.1</strong> Under the Data Protection Legislation, we must always have a lawful basis for collecting your personal data. The following table describes how we may use your personal data, and our lawful bases for doing so depending on the type of user:
                  </p>
                  
                  <div className="mb-6">
                    <h3 className="text-base font-semibold text-novaNeutral-900 mb-3">General Users and Nova Platform Users:</h3>
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full border border-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="border border-gray-300 px-4 py-2 text-left">What We Do</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">What Data we Use</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">Our Lawful Basis</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">Registering you on Our Site.</td>
                            <td className="border border-gray-300 px-4 py-2">Name, business name, business address, business email and telephone number.</td>
                            <td className="border border-gray-300 px-4 py-2">Contract, for the purpose of delivering our services.</td>
                          </tr>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">Sending marketing materials.</td>
                            <td className="border border-gray-300 px-4 py-2">Contact details such as your name, email address, business address and telephone number.</td>
                            <td className="border border-gray-300 px-4 py-2">Specific, informed consent.</td>
                          </tr>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">Supplying our products AND/OR services to you.</td>
                            <td className="border border-gray-300 px-4 py-2">As above and including business bank account and card details.</td>
                            <td className="border border-gray-300 px-4 py-2">Contract, for the purpose of delivering our services.</td>
                          </tr>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">For Nova Platform Users, allowing access to, and use of, our Nova Applications.</td>
                            <td className="border border-gray-300 px-4 py-2">Sensitive information personally identifying you.</td>
                            <td className="border border-gray-300 px-4 py-2">Contract, for the purpose of delivering our services.</td>
                          </tr>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">For Nova Platform Users, allowing access to, and continued use of our Nova Applications</td>
                            <td className="border border-gray-300 px-4 py-2">Special category data which may include details of health, children or convictions.</td>
                            <td className="border border-gray-300 px-4 py-2">Contract, for the purpose of delivering our services.</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="text-base font-semibold text-novaNeutral-900 mb-3">Law Firm Users:</h3>
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full border border-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="border border-gray-300 px-4 py-2 text-left">What We Do</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">What Data we Use</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">Our Lawful Basis</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">Providing and managing your Account.</td>
                            <td className="border border-gray-300 px-4 py-2">Name, business name, business address, business email and telephone number.</td>
                            <td className="border border-gray-300 px-4 py-2">Contract, for the purpose of delivering our services.</td>
                          </tr>
                          <tr>
                            <td className="border border-gray-300 px-4 py-2">Supplying our products AND/OR services to you.</td>
                            <td className="border border-gray-300 px-4 py-2">As above and including business bank account and card details.</td>
                            <td className="border border-gray-300 px-4 py-2">Contract, for the purpose of delivering our services.</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <p className="mb-4">
                    <strong className="mr-1">6.2</strong> For Nova Platform Users, sensitive information (that identifies you) will be obtained from your use of our Nova Applications, but this information will not be accessible to other site visitors. Nor will it be accessible to site administrative or technical support staff except for specified individuals who will access it only for the following purposes:
                  </p>
                  <ul className="space-y-2 ml-4 mb-4 pl-6 list-[lower-alpha] [&>li::marker]:content-[counter(list-item,lower-alpha)_')_']">
                    <li> To re-send information to you at your specific request in the event you have mislaid your submission;</li>
                    <li> To send or re-send the information you have saved to your chosen solicitor or barrister;</li>
                    <li> To assist you in the completion of a submission if you experience technical problems;</li>
                    <li> To strip out all and any information that identifies you before using anonymised data for analytics purposes.</li>
                  </ul>
                  <p className="mb-4">
                    <strong className="mr-1">6.3</strong> We will only use your personal data for the purpose(s) for which it was originally collected unless we reasonably believe that another purpose is compatible with that or those original purpose(s) and need to use your personal data for that purpose
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">6.4</strong> If we need to use your personal data for a purpose that is unrelated to, or incompatible with, the purpose(s) for which it was originally collected, we will inform you and explain the legal basis which allows us to do so.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">6.5</strong> In some circumstances, where permitted or required by law, we may process your personal data without your knowledge or consent. This will only be done within the bounds of the Data Protection Legislation and your legal rights.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">7. Automated Decision Making</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">7.1</strong> Although we use automated system(s) we do not do so for the carrying out of certain kinds of decision-making and/or profiling.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">8. How Long Will You Keep My Personal Data?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">8.1</strong> We will not keep your personal data for any longer than is necessary in light of the reason(s) for which it was first collected. Your personal data will therefore be kept for the following periods (or, where there is no fixed period, the following factors will be used to determine how long it is kept):
                  </p>
                  <div className="overflow-x-auto mb-4">
                    <table className="min-w-full border border-gray-300">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="border border-gray-300 px-4 py-2 text-left">Type of Data</th>
                          <th className="border border-gray-300 px-4 py-2 text-left">How Long We Keep It</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="border border-gray-300 px-4 py-2">For Nova Platform Users, identifying information such as names, date of birth and gender</td>
                          <td className="border border-gray-300 px-4 py-2">In an identifiable state for two years and thereafter anonymised.</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">9. How and Where Do You Store or Transfer My Personal Data?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">9.1</strong> We will only store your personal data in the UK.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">9.2</strong> We hold your personal data in a combination of hard copy and electronic files for the period necessary to support Our Site, comply with our legal obligations, resolve disputes, or otherwise fulfill the purposes outlined in this Policy.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">9.3</strong> We may also retain backup information on our servers for some time in order to comply with applicable laws and regulations, and our internal security policies and procedures. Where applicable, we do not always remove or delete all of your personal data for a number of reasons including due to technical and system constraints, contractual requirements or legal requirements.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">9.4</strong> At the end of the above data retention periods, all of the data stored, including personal data, will be reviewed and securely delete/destroyed.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">9.5</strong> Please note that no method of transmission over the internet, method of electronic storage or other security methods are 100% secure. Therefore, while we strive to use commercially acceptable means of security, such as firewalls, encrypted databases with limited physical and electronic access, and other encryption methods, to protect your personal data against unauthorised use, disclosure or modification, we cannot guarantee its absolute security.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">10. Data Security</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">10.1</strong> The security of your personal data is essential to us, and to protect your data, we take a number of important measures, including the following:
                  </p>
                  <ul className="space-y-2 ml-4 mb-4 pl-6 list-[lower-alpha] [&>li::marker]:content-[counter(list-item,lower-alpha)_')_']">
                    <li> Limiting access to your personal data to those employees, agents, contractors, and other third parties with a legitimate need to know and ensuring that they are subject to duties of confidentiality; and where necessary to sub-processor agreements.</li>
                    <li> Procedures for dealing with data breaches (the accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to, your personal data) including notifying you and/or the Information Commissioner's Office where legally required to do so;</li>
                    <li> Secure Socket Layer encryption to access Our Site.</li>
                    <li> All data is encrypted at rest and in transit.</li>
                    <li> There are enforced log-in procedures for Nova Platform Users.</li>
                  </ul>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">11. Do You Share My Personal Data?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">11.1</strong> We may share the personal data of General Visitors or Law Firms with the below third-party processors, for more information on this, please review the third party privacy policies below:
                  </p>
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-novaNeutral-900 mb-2">LinkedIn Marketing Solutions.</h3>
                    <p className="mb-4">We use LinkedIn Marketing Solutions, including the LinkedIn Insight Tag, Lead Gen Forms, Matched Audiences, and Conversions API, to measure campaign performance and show relevant ads. For personal data collected via these tools, LinkedIn acts as an independent controller and processes that data for its own purposes such as ad delivery, reporting, and improving its services.</p>
                    
                    <h3 className="text-lg font-semibold text-novaNeutral-900 mb-2">Cookies/Consent</h3>
                    <p className="mb-4">These tools may set cookies or use similar technologies on our pages. Where required by law, we obtain your consent before activating non-essential cookies. You can manage your preferences via our cookie banner at any time.</p>
                    
                    <h3 className="text-lg font-semibold text-novaNeutral-900 mb-2">Your Data With Us</h3>
                    <p className="mb-4">We remain the controller of any data we collect directly from you (e.g., form submissions on our site and CRM records). To exercise your rights in relation to data processed by us, contact our Data Protection Officer (details in paragraph 2 above). To exercise your rights in relation to data processed by LinkedIn, please contact LinkedIn directly via its privacy resources.</p>
                    
                    <h3 className="text-lg font-semibold text-novaNeutral-900 mb-2">International Transfers</h3>
                    <p className="mb-4">Where LinkedIn transfers personal data internationally, it relies on appropriate safeguards (e.g., Standard Contractual Clauses/UK IDTA) as described in LinkedIn's privacy documentation.</p>
                  </div>
                  <p className="mb-4">
                    <strong className="mr-1">11.2</strong> If we sell, transfer, or merge parts of our business or assets, your personal data may be transferred to a third party. Any new owner of our business may continue to use your personal data in the same way(s) that we have used it, as specified in this Privacy Policy.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">11.3</strong> In some limited circumstances, we may be legally required to share certain personal data, which might include yours, if we are involved in legal proceedings or complying with legal obligations, a court order, or the instructions of a government authority.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">11.4</strong> If you are a Nova Platform User your data will be shared with your chosen lawyers (if applicable) via our Nova Applications and we will take steps to ensure that your personal data is handled safely, securely, and in accordance with your rights, and our obligations.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">12. What Are My Rights?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">12.1</strong> Under the Data Protection Legislation, you have the following rights, which we will always work to uphold. Should you wish to exercise any of the below rights please contact us using the contact details set out at the top of this policy
                  </p>
                  <ol className="list-outside space-y-2 ml-4 mb-4 pl-6 list-[lower-alpha] [&>li::marker]:content-[counter(list-item,lower-alpha)_')_']">
                    <li> The right to be informed about our collection and use of your personal data. This Privacy Policy should tell you everything you need to know, but you can always contact us to find out more or to ask any questions using the contact details at the top of this Privacy Policy.</li>
                    <li> The right to access the personal data we hold about you.</li>
                    <li> The right to have your personal data rectified if any of your personal data held by us is inaccurate or incomplete.</li>
                    <li> The right to be forgotten, i.e. the right to ask us to delete or otherwise dispose of any of your personal data that we hold.</li>
                    <li> The right to restrict (i.e. prevent) the processing of your personal data.</li>
                    <li> The right to object to us using your personal data for a particular purpose or purposes.</li>
                    <li> The right to withdraw consent. This means that, if we are relying on your consent as the legal basis for using your personal data, you are free to withdraw that consent at any time.</li>
                    <li> The right to data portability. This means that, if you have provided personal data to us directly, where we are using it with your consent or for the performance of a contract, and that data is processed using automated means, you can ask us for a copy of that personal data to re-use with another service or business in many cases.</li>
                    <li> Rights relating to automated decision-making and profiling.</li>
                  </ol>
                  <p className="mb-4">
                    <strong className="mr-1">12.2</strong> For more information about our use of your personal data or exercising your rights as outlined above, please contact us using the details provided at the start of this Privacy Policy.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">12.3</strong> If you have a concern about your privacy or would like to know more about how your personally identifiable information is collected or used, please contact us using the information at the top of this policy. We ask that when you contact us with a complaint, please include contact information and clearly describe your complaint.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">12.4</strong> We will respond to your request or complaint within a reasonable time and will let you know the next steps in resolving your complaint. If you are not satisfied with our response, you may also contact your local and federal data protection authorities to lodge a complaint.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">13. Can I Withhold Information?</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">13.1</strong> You may access certain areas of Our Site without providing any personal data at all. However, to use all features and functions available on Our Site you may be required to submit or allow for the collection of certain data.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">13.2</strong> You may restrict our use of Cookies. For more information, please refer to our <a href="/cookie-policy" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">Cookie Policy</a>.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">14. Changes to this Privacy Policy</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">14.1</strong> We may change this Privacy Policy from time to time. This may be necessary, for example, if the law changes, or if we change our business in a way that affects personal data protection.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">14.2</strong> Any changes will be immediately posted on Our Site and you will be deemed to have accepted the terms of the Privacy Policy on your first use of Our Site following the alterations. We recommend that you check this page regularly to keep up-to-date.
                  </p>
                  <p className="mb-4">
                    <strong className="mr-1">14.3</strong> This Privacy Policy was last updated on 25 October 2025.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">15. Disclaimer</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    <strong className="mr-1">15.1</strong> For the avoidance of doubt, the services on Our Site, including but not limited to the services utilised by Nova Platform Users, do not constitute legal advice and should not be relied upon as the basis for any action subsequently taken by a site visitor or user.
                  </p>
                </div>
              </section>
            </div>
          </div>
        </div>
      </main>
      <LandingFooter/>
    </div>
  );
};

export default PrivacyPolicy;
