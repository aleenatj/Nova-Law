## Alerts

Display messages to users.

```typescript
import { createSuccessAlert, AlertContainer } from '@/utils';

// Create alerts
const alert = createSuccessAlert('Title', 'Message', 5000); // duration optional
const errorAlert = createErrorAlert('Error', 'Failed');
const warningAlert = createWarningAlert('Warning', 'Check input');
const infoAlert = createInfoAlert('Info', 'Loading...');

// Render
<AlertContainer alerts={alerts} onDismiss={(id) => removeAlert(id)} />
```
-----------------------------------------------------------------------------------------------
## Toasts

Quick notifications with global management.

```typescript
import { createSuccessToast, toastManager } from '@/utils';

// Simple usage - toasts appear globally
const toast = createSuccessToast('Success', 'Operation completed!');
toastManager.addToast(toast);

// Or use the helper functions
toastManager.addToast(createErrorToast('Error', 'Something went wrong'));
toastManager.addToast(createWarningToast('Warning', 'Please check your input'));
toastManager.addToast(createInfoToast('Info', 'Loading...'));

// The GlobalToastContainer in App.tsx handles rendering automatically
```

**Note:** The `GlobalToastContainer` is already added to `App.tsx`, so toasts will appear automatically without needing to add any components to your pages.
-----------------------------------------------------------------------------------------------
## Form Validation

Validate user input.

```typescript
import { FormValidator, useFormValidation } from '@/utils';

// Schema
const schema = {
  email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
  password: { required: true, minLength: 8 }
};

// Component usage
<FormValidator schema={schema} onSubmit={(data) => console.log(data)}>
  {({ formData, errors, touched, isValid, handleChange, handleBlur, handleSubmit }) => (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      <input
        value={formData.email || ''}
        onChange={(e) => handleChange('email', e.target.value)}
        onBlur={() => handleBlur('email')}
      />
      {touched.email && errors.email && <p>{errors.email.errors.join(', ')}</p>}
      <button disabled={!isValid}>Submit</button>
    </form>
  )}
</FormValidator>

// Hook usage
const { formData, errors, isValid, handleChange, handleSubmit } = useFormValidation(schema);
```
-----------------------------------------------------------------------------------------------
## Pagination

Page-based navigation.

```typescript
import { usePagination, Pagination, getPageItems } from '@/utils';

// Setup
const pagination = usePagination(totalItems, itemsPerPage);
const currentItems = getPageItems(allItems, pagination.currentPage, itemsPerPage);

// Render
<Pagination
  config={{
    currentPage: pagination.currentPage,
    totalPages: pagination.totalPages,
    totalItems: pagination.totalItems,
    itemsPerPage: pagination.itemsPerPage,
    onPageChange: pagination.goToPage
  }}
/>

// Navigation
pagination.goToPage(5);
pagination.goToNextPage();
pagination.goToPreviousPage();
```
-----------------------------------------------------------------------------------------------
## Storage Helpers

Manage localStorage.

```typescript
import { saveToLocalStorage, getFromLocalStorage, removeFromLocalStorage } from '@/utils';

// Save data
saveToLocalStorage('key', value);

// Get data
const data = getFromLocalStorage('key', defaultValue);

// Remove data
removeFromLocalStorage('key');
```
-----------------------------------------------------------------------------------------------
## Dynamic Components

Load components by type.

```typescript
import { DynamicComponentLoader, createComponentMap } from '@/utils';

// Create map
const components = createComponentMap({
  user: UserComponent,
  product: ProductComponent
});

// Use
<DynamicComponentLoader
  item={{ type: 'user', name: 'John' }}
  components={components}
  fallbackComponent={DefaultComponent} // optional
/>
```