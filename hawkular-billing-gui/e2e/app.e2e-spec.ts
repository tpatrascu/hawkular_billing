import { HawkularBillingGuiPage } from './app.po';

describe('hawkular-billing-gui App', () => {
  let page: HawkularBillingGuiPage;

  beforeEach(() => {
    page = new HawkularBillingGuiPage();
  });

  it('should display welcome message', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('Welcome to app!!');
  });
});
